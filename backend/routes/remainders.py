"""
Remainders routes for PingDoc - API endpoints for managing follow-up reminders
"""

from fastapi import APIRouter, HTTPException
from backend.models.remainders import Remainder, RemainderCreate, RemainderUpdate
from backend.database import db
from backend.services.scheduler_service import scheduler_service
from backend.agents import agent_registry
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/remainders", tags=["remainders"])

@router.post("/", response_model=dict)
async def create_remainder(remainder: RemainderCreate, doctor_id: str):
    """Create a new follow-up reminder and schedule it automatically"""
    try:
        # Validate that followup_date is in the future
        if remainder.followup_date <= datetime.now():
            raise HTTPException(
                status_code=400, 
                detail="Follow-up date must be in the future"
            )
        
        # Check if patient exists
        patient = db.patients.find_one({"_id": remainder.patient_id, "doctor_id": doctor_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create remainder record
        remainder_data = {
            "doctor_id": doctor_id,
            "patient_id": remainder.patient_id,
            "followup_date": remainder.followup_date,
            "message_template": remainder.message_template,
            "status": "pending",
            "created_at": datetime.now(),
            "scheduled_job_id": None,
            "attempts": 0,
            "last_attempt": None,
            "error_message": None
        }
        
        result = db.remainders.insert_one(remainder_data)
        remainder_id = str(result.inserted_id)
        
        # Schedule the follow-up reminder (24 hours before appointment)
        job_id = await scheduler_service.schedule_follow_up_reminder(
            remainder_id=remainder_id,
            patient_id=remainder.patient_id,
            doctor_id=doctor_id,
            followup_datetime=remainder.followup_date,
            advance_hours=24
        )
        
        if job_id:
            logger.info(f"✅ Remainder created and scheduled: {remainder_id} (Job: {job_id})")
            return {
                "success": True,
                "remainder_id": remainder_id,
                "scheduled_job_id": job_id,
                "reminder_time": (remainder.followup_date - timedelta(hours=24)).isoformat(),
                "followup_time": remainder.followup_date.isoformat(),
                "patient_name": patient.get("name", "Unknown"),
                "message": "Follow-up reminder created and scheduled successfully"
            }
        else:
            return {
                "success": True,
                "remainder_id": remainder_id,
                "scheduled_job_id": None,
                "warning": "Remainder created but scheduling failed",
                "message": "Manual reminder may be needed"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating remainder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[dict])
def get_remainders(doctor_id: str, status: Optional[str] = None):
    """Get all remainders for a doctor, optionally filtered by status"""
    try:
        # Build query
        query = {"doctor_id": doctor_id}
        if status:
            query["status"] = status
        
        # Get remainders
        remainders = list(db.remainders.find(query).sort("followup_date", 1))
        
        # Enrich with patient information
        enriched_remainders = []
        for remainder in remainders:
            patient = db.patients.find_one({"_id": remainder["patient_id"]})
            if patient:
                remainder["patient_name"] = patient.get("name", "Unknown")
                remainder["patient_phone"] = patient.get("phone", "Unknown")
                remainder["patient_diagnosis"] = patient.get("diagnosis", "Unknown")
            
            # Convert ObjectId to string
            remainder["_id"] = str(remainder["_id"])
            enriched_remainders.append(remainder)
        
        return enriched_remainders
        
    except Exception as e:
        logger.error(f"Error getting remainders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{remainder_id}", response_model=dict)
def get_remainder(remainder_id: str, doctor_id: str):
    """Get a specific remainder by ID"""
    try:
        # Get remainder
        remainder = db.remainders.find_one({
            "_id": remainder_id,
            "doctor_id": doctor_id
        })
        
        if not remainder:
            raise HTTPException(status_code=404, detail="Remainder not found")
        
        # Get patient information
        patient = db.patients.find_one({"_id": remainder["patient_id"]})
        if patient:
            remainder["patient_name"] = patient.get("name", "Unknown")
            remainder["patient_phone"] = patient.get("phone", "Unknown")
            remainder["patient_diagnosis"] = patient.get("diagnosis", "Unknown")
        
        # Convert ObjectId to string
        remainder["_id"] = str(remainder["_id"])
        
        return remainder
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting remainder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{remainder_id}", response_model=dict)
async def update_remainder(remainder_id: str, update_data: RemainderUpdate, doctor_id: str):
    """Update a remainder and reschedule if necessary"""
    try:
        # Get existing remainder
        existing_remainder = db.remainders.find_one({
            "_id": remainder_id,
            "doctor_id": doctor_id
        })
        
        if not existing_remainder:
            raise HTTPException(status_code=404, detail="Remainder not found")
        
        # Prepare update data
        update_fields = {}
        if update_data.followup_date is not None:
            if update_data.followup_date <= datetime.now():
                raise HTTPException(
                    status_code=400,
                    detail="Follow-up date must be in the future"
                )
            update_fields["followup_date"] = update_data.followup_date
        
        if update_data.message_template is not None:
            update_fields["message_template"] = update_data.message_template
        
        if update_data.status is not None:
            update_fields["status"] = update_data.status
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update the remainder
        db.remainders.update_one(
            {"_id": remainder_id},
            {"$set": update_fields}
        )
        
        # If followup_date changed, reschedule the reminder
        new_job_id = None
        if update_data.followup_date is not None:
            old_job_id = existing_remainder.get("scheduled_job_id")
            if old_job_id:
                new_job_id = await scheduler_service.reschedule_follow_up_reminder(
                    remainder_id=remainder_id,
                    old_job_id=old_job_id,
                    new_followup_datetime=update_data.followup_date,
                    patient_id=existing_remainder["patient_id"],
                    doctor_id=doctor_id
                )
        
        # Get updated remainder
        updated_remainder = db.remainders.find_one({"_id": remainder_id})
        updated_remainder["_id"] = str(updated_remainder["_id"])
        
        return {
            "success": True,
            "remainder": updated_remainder,
            "rescheduled": new_job_id is not None,
            "new_job_id": new_job_id,
            "message": "Remainder updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating remainder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{remainder_id}")
async def delete_remainder(remainder_id: str, doctor_id: str):
    """Delete a remainder and cancel its scheduled job"""
    try:
        # Get remainder to find job ID
        remainder = db.remainders.find_one({
            "_id": remainder_id,
            "doctor_id": doctor_id
        })
        
        if not remainder:
            raise HTTPException(status_code=404, detail="Remainder not found")
        
        # Cancel scheduled job if exists
        job_id = remainder.get("scheduled_job_id")
        if job_id:
            await scheduler_service.cancel_follow_up_reminder(job_id)
        
        # Delete remainder
        result = db.remainders.delete_one({
            "_id": remainder_id,
            "doctor_id": doctor_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Remainder not found")
        
        return {
            "success": True,
            "message": "Remainder deleted and job cancelled successfully",
            "cancelled_job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting remainder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{remainder_id}/send-now")
async def send_remainder_now(remainder_id: str, doctor_id: str):
    """Send a remainder immediately (manual trigger)"""
    try:
        # Get remainder
        remainder = db.remainders.find_one({
            "_id": remainder_id,
            "doctor_id": doctor_id
        })
        
        if not remainder:
            raise HTTPException(status_code=404, detail="Remainder not found")
        
        # Send the reminder immediately
        result = await agent_registry.send_follow_up_reminder(
            remainder["patient_id"],
            doctor_id,
            remainder["followup_date"].isoformat()
        )
        
        if result.get("success"):
            # Update remainder status
            db.remainders.update_one(
                {"_id": remainder_id},
                {"$set": {
                    "status": "sent",
                    "last_attempt": datetime.now(),
                    "$inc": {"attempts": 1}
                }}
            )
            
            return {
                "success": True,
                "message": f"Reminder sent immediately to {result.get('patient_name', 'patient')}",
                "send_result": result
            }
        else:
            # Update remainder with error
            db.remainders.update_one(
                {"_id": remainder_id},
                {"$set": {
                    "status": "failed",
                    "error_message": result.get("error", "Unknown error"),
                    "last_attempt": datetime.now(),
                    "$inc": {"attempts": 1}
                }}
            )
            
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send reminder: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending remainder now: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{doctor_id}")
def get_remainder_stats(doctor_id: str):
    """Get remainder statistics for a doctor"""
    try:
        # Get counts by status
        pipeline = [
            {"$match": {"doctor_id": doctor_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_counts = {}
        for result in db.remainders.aggregate(pipeline):
            status_counts[result["_id"]] = result["count"]
        
        # Get upcoming remainders (next 7 days)
        upcoming_date = datetime.now() + timedelta(days=7)
        upcoming_count = db.remainders.count_documents({
            "doctor_id": doctor_id,
            "followup_date": {"$lte": upcoming_date},
            "status": {"$in": ["pending", "scheduled"]}
        })
        
        # Get overdue remainders (past due but not sent)
        overdue_count = db.remainders.count_documents({
            "doctor_id": doctor_id,
            "followup_date": {"$lt": datetime.now()},
            "status": {"$in": ["pending", "failed"]}
        })
        
        return {
            "total_remainders": sum(status_counts.values()),
            "status_breakdown": status_counts,
            "upcoming_remainders": upcoming_count,
            "overdue_remainders": overdue_count,
            "success_rate": (
                status_counts.get("sent", 0) / sum(status_counts.values()) * 100
                if sum(status_counts.values()) > 0 else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting remainder stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
