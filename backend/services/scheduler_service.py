"""
Background Scheduler Service for DocFollow - Handles automated follow-up scheduling
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import asyncio
from backend.config import MONGODB_URI, MONGODB_DB_NAME
from backend.database import db
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)

def _cleanup_old_jobs():
    """Clean up old completed/failed followup records"""
    try:
        # Remove followups older than 30 days that are completed or failed
        cutoff_date = datetime.now() - timedelta(days=30)
        
        result = db.followups.delete_many({
            "created_at": {"$lt": cutoff_date},
            "status": {"$in": ["sent", "failed", "completed"]}
        })
        
        logger.info(f"🧹 Cleaned up {result.deleted_count} old followup records")
        
    except Exception as e:
        logger.error(f"❌ Error in cleanup job: {str(e)}")

async def _send_follow_up_reminder(
    followup_id: str,
    patient_id: str,
    doctor_id: str,
    followup_datetime_str: str
):
    """
    Internal method to send follow-up reminder (called by scheduler)
    
    Args:
        followup_id: Database ID of the followup record
        patient_id: Patient's database ID
        doctor_id: Doctor's database ID
        followup_datetime_str: Follow-up datetime as ISO string
    """
    try:
        logger.info(f"🕒 Executing scheduled follow-up for followup {followup_id}")
        
        # Update followup status to sending
        db.followups.update_one(
            {"_id": followup_id},
            {"$set": {
                "status": "processing",
                "last_attempt": datetime.now(),
                "$inc": {"attempts": 1}
            }}
        )
        
        # Import agent_registry here to avoid circular imports
        from backend.agents import agent_registry
        
        follow_up_agent = agent_registry.get_follow_up_agent()
        if not follow_up_agent:
            raise Exception("Follow-up agent not available")

        result = await follow_up_agent.trigger_follow_up(patient_id, doctor_id, followup_id)
        
        if result.get("success"):
            # Update followup status to sent
            db.followups.update_one(
                {"_id": followup_id},
                {"$set": {"status": "completed"}}
            )
            logger.info(f"✅ Follow-up triggered successfully for followup {followup_id}")
        else:
            # Update followup status to failed
            db.followups.update_one(
                {"_id": followup_id},
                {"$set": {
                    "status": "failed",
                    "error_message": result.get("error", "Unknown error")
                }}
            )
            logger.error(f"❌ Failed to trigger follow-up for followup {followup_id}: {result.get('error')}")
        
    except Exception as e:
        # Update followup status to failed
        db.followups.update_one(
            {"_id": followup_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e)
            }}
        )
        logger.error(f"❌ Exception in _send_follow_up_reminder for followup {followup_id}: {str(e)}")

class SchedulerService:
    """
    Background scheduler service for managing automated follow-up reminders
    """
    
    def __init__(self):
        """Initialize the scheduler service"""
        self.scheduler = None
        self.db = db  # Use existing database connection
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the scheduler with MongoDB job store
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            logger.info("Scheduler already initialized")
            return True
        
        try:
            # Database already set in __init__
            
            # Configure job stores
            jobstores = {
                'default': MongoDBJobStore(database=MONGODB_DB_NAME, collection='scheduled_jobs', host=MONGODB_URI)
            }
            
            # Configure executors  
            executors = {
                'default': ThreadPoolExecutor(20),
                'processpool': ProcessPoolExecutor(5)
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': False,
                'max_instances': 3,
                'misfire_grace_time': 30
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
            )
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
            
            # Start scheduler
            self.scheduler.start()
            
            self._initialized = True
            logger.info("✅ Scheduler service initialized successfully")
            
            # Schedule cleanup job to run daily
            await self._schedule_cleanup_job()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scheduler service: {str(e)}")
            return False
    
    async def schedule_follow_up_reminder(
        self,
        remainder_id: str,
        patient_id: str,
        doctor_id: str,
        followup_datetime: datetime,
    ) -> Optional[str]:
        """
        Schedule a follow-up reminder to be sent before the appointment
        
        Args:
            remainder_id: Database ID of the followup record
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            followup_datetime: The actual follow-up appointment time
            
        Returns:
            str: Job ID if scheduled successfully, None if failed
        """
        if not self._initialized:
            logger.error("Scheduler not initialized")
            return None
        
        try:
            # Calculate reminder time
            reminder_time = followup_datetime
            
            # Don't schedule if reminder time is in the past
            if reminder_time <= datetime.utcnow():
                logger.warning(f"Reminder time {reminder_time} is in the past, scheduling immediately")
                reminder_time = datetime.utcnow() + timedelta(seconds=30)  # Schedule 30 seconds from now
            
            # Create job ID
            job_id = f"followup_reminder_{remainder_id}_{int(datetime.utcnow().timestamp())}"
            
            # Schedule the job
            job = self.scheduler.add_job(
                func=_send_follow_up_reminder,
                trigger='date',
                run_date=reminder_time,
                args=[remainder_id, patient_id, doctor_id, followup_datetime.isoformat()],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=300  # 5 minutes grace time
            )
            
            # Update followup record with job ID
            self.db.followups.update_one(
                {"_id": remainder_id},
                {"$set": {"scheduled_job_id": job_id}}
            )
            
            logger.info(f"✅ Scheduled follow-up reminder for {reminder_time} (Job ID: {job_id})")
            return job_id
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule follow-up reminder: {str(e)}")
            return None
    
    async def cancel_follow_up_reminder(self, job_id: str) -> bool:
        """
        Cancel a scheduled follow-up reminder
        
        Args:
            job_id: The scheduler job ID
            
        Returns:
            bool: True if cancelled successfully
        """
        if not self._initialized:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"✅ Cancelled follow-up reminder job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel job {job_id}: {str(e)}")
            return False
    
    async def reschedule_follow_up_reminder(
        self,
        remainder_id: str,
        old_job_id: str,
        new_followup_datetime: datetime,
        patient_id: str,
        doctor_id: str,
    ) -> Optional[str]:
        """
        Reschedule an existing follow-up reminder
        
        Args:
            remainder_id: Database ID of the followup record
            old_job_id: Previous job ID to cancel
            new_followup_datetime: New follow-up appointment time
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            
        Returns:
            str: New job ID if rescheduled successfully
        """
        try:
            # Cancel old job
            await self.cancel_follow_up_reminder(old_job_id)
            
            # Schedule new job
            new_job_id = await self.schedule_follow_up_reminder(
                remainder_id, patient_id, doctor_id, new_followup_datetime
            )
            
            return new_job_id
            
        except Exception as e:
            logger.error(f"❌ Failed to reschedule follow-up reminder: {str(e)}")
            return None
    
    async def _schedule_cleanup_job(self):
        """Schedule a daily cleanup job to remove old completed jobs"""
        try:
            self.scheduler.add_job(
                func=_cleanup_old_jobs,
                trigger='cron',
                hour=2,  # Run at 2 AM daily
                minute=0,
                id='daily_cleanup',
                replace_existing=True
            )
            logger.info("✅ Scheduled daily cleanup job")
        except Exception as e:
            logger.error(f"❌ Failed to schedule cleanup job: {str(e)}")
    
    def _job_executed(self, event):
        """Event listener for successful job execution"""
        logger.info(f"✅ Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Event listener for job execution errors"""
        logger.error(f"❌ Job {event.job_id} failed with error: {event.exception}")
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """
        Get information about all scheduled jobs
        
        Returns:
            Dict containing job information
        """
        if not self._initialized:
            return {"error": "Scheduler not initialized"}
        
        try:
            jobs = self.scheduler.get_jobs()
            job_info = []
            
            for job in jobs:
                job_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
            
            return {
                "total_jobs": len(jobs),
                "jobs": job_info
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduled jobs: {str(e)}")
            return {"error": str(e)}
    
    def is_initialized(self) -> bool:
        """Check if scheduler is initialized"""
        return self._initialized
    
    async def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler and self._initialized:
            logger.info("🛑 Shutting down scheduler...")
            self.scheduler.shutdown(wait=True)
            self._initialized = False
            logger.info("✅ Scheduler shutdown complete")


# Global instance
scheduler_service = SchedulerService()
