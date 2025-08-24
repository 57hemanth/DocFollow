from fastapi import APIRouter, Body, HTTPException, status
from typing import List, Dict, Any, Optional
from backend.schemas.followups import Followup, FollowupCreate, FollowupUpdate
from backend.database import db
from bson import ObjectId
from backend.services.scheduler_service import scheduler_service
from backend.agents import agent_registry
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/followups", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_followup(followup: FollowupCreate):
    """Create a new follow-up and schedule its reminder"""
    try:
        if followup.followup_date <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Follow-up date must be in the future")
        
        patient = db.patients.find_one({"_id": ObjectId(followup.patient_id)})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        followup_data = {
            "doctor_id": followup.doctor_id,
            "patient_id": followup.patient_id,
            "followup_date": followup.followup_date,
            "message_template": followup.message_template,
            "status": "pending",
            "created_at": datetime.now(),
        }
        
        result = db.followups.insert_one(followup_data)
        followup_id = str(result.inserted_id)
        
        job_id = await scheduler_service.schedule_follow_up_reminder(
            remainder_id=followup_id,
            patient_id=followup.patient_id,
            doctor_id=followup.doctor_id,
            followup_datetime=followup.followup_date
        )
        
        db.followups.update_one({"_id": ObjectId(followup_id)}, {"$set": {"scheduled_job_id": job_id}})
        
        return {
            "success": True,
            "followup_id": followup_id,
            "scheduled_job_id": job_id,
            "patient_name": patient.get("name", "Unknown"),
            "message": "Follow-up created and scheduled successfully"
        }
    except Exception as e:
        logger.error(f"Error creating followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followups", response_model=List[Dict[str, Any]])
def get_followups(doctor_id: str, status: Optional[str] = None):
    """Get all follow-ups for a doctor, optionally filtered by status"""
    try:
        query = {"doctor_id": doctor_id}
        if status:
            query["status"] = status
            
        followups = list(db.followups.find(query).sort("followup_date", 1))
        
        enriched_followups = []
        for followup in followups:
            patient = db.patients.find_one({"_id": ObjectId(followup["patient_id"])})
            if patient:
                followup["patient_name"] = patient.get("name", "Unknown")
                followup["patient_phone"] = patient.get("phone", "Unknown")
                followup["patient_diagnosis"] = patient.get("diagnosis", "Unknown")
            
            followup["_id"] = str(followup["_id"])
            enriched_followups.append(followup)
            
        return enriched_followups
    except Exception as e:
        logger.error(f"Error getting followups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followups/{followup_id}", response_model=Dict[str, Any])
def get_followup(followup_id: str, doctor_id: str):
    """Get a specific followup by ID"""
    try:
        followup = db.followups.find_one({"_id": ObjectId(followup_id), "doctor_id": doctor_id})
        
        if not followup:
            raise HTTPException(status_code=404, detail="Followup not found")
        
        patient = db.patients.find_one({"_id": ObjectId(followup["patient_id"])})
        if patient:
            followup["patient_name"] = patient.get("name", "Unknown")

        followup["_id"] = str(followup["_id"])
        return followup
    except Exception as e:
        logger.error(f"Error getting followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/followups/{followup_id}", response_model=Dict[str, Any])
async def update_followup(followup_id: str, update_data: FollowupUpdate):
    """Update a followup and reschedule if necessary"""
    try:
        existing_followup = db.followups.find_one({"_id": ObjectId(followup_id)})
        
        if not existing_followup:
            raise HTTPException(status_code=404, detail="Followup not found")
            
        update_fields = update_data.dict(exclude_unset=True)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        db.followups.update_one({"_id": ObjectId(followup_id)}, {"$set": update_fields})
        
        new_job_id = None
        if 'followup_date' in update_fields:
            old_job_id = existing_followup.get("scheduled_job_id")
            if old_job_id:
                new_job_id = await scheduler_service.reschedule_follow_up_reminder(
                    remainder_id=followup_id,
                    old_job_id=old_job_id,
                    new_followup_datetime=update_fields['followup_date'],
                    patient_id=existing_followup["patient_id"],
                    doctor_id=update_data.doctor_id
                )
        
        updated_followup = db.followups.find_one({"_id": ObjectId(followup_id)})
        updated_followup["_id"] = str(updated_followup["_id"])
        
        return {
            "success": True,
            "followup": updated_followup,
            "rescheduled": new_job_id is not None,
            "new_job_id": new_job_id
        }
    except Exception as e:
        logger.error(f"Error updating followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/followups/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_followup(followup_id: str, doctor_id: str):
    """Delete a followup and cancel its scheduled job"""
    try:
        followup = db.followups.find_one({"_id": ObjectId(followup_id), "doctor_id": doctor_id})
        
        if not followup:
            raise HTTPException(status_code=404, detail="Followup not found")
        
        job_id = followup.get("scheduled_job_id")
        if job_id:
            await scheduler_service.cancel_follow_up_reminder(job_id)
            
        db.followups.delete_one({"_id": ObjectId(followup_id)})
        
    except Exception as e:
        logger.error(f"Error deleting followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/followups/{followup_id}/send-now", response_model=Dict[str, Any])
async def send_followup_now(followup_id: str, doctor_id: str):
    """Send a followup reminder immediately"""
    try:
        followup = db.followups.find_one({"_id": ObjectId(followup_id), "doctor_id": doctor_id})
        
        if not followup:
            raise HTTPException(status_code=404, detail="Followup not found")
        
        result = await agent_registry.send_follow_up_reminder(
            followup["patient_id"],
            doctor_id,
            followup["followup_date"].isoformat()
        )
        
        if result.get("success"):
            db.followups.update_one(
                {"_id": ObjectId(followup_id)},
                {"$set": {"status": "sent", "last_attempt": datetime.now()}, "$inc": {"attempts": 1}}
            )
            return {"success": True, "message": "Followup sent successfully"}
        else:
            db.followups.update_one(
                {"_id": ObjectId(followup_id)},
                {"$set": {"status": "failed", "error_message": result.get("error"), "last_attempt": datetime.now()}, "$inc": {"attempts": 1}}
            )
            raise HTTPException(status_code=400, detail=f"Failed to send followup: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error sending followup now: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followups/stats/{doctor_id}", response_model=Dict[str, Any])
def get_followup_stats(doctor_id: str):
    """Get followup statistics for a doctor"""
    try:
        pipeline = [
            {"$match": {"doctor_id": doctor_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        status_counts = {item["_id"]: item["count"] for item in db.followups.aggregate(pipeline)}
        
        upcoming_count = db.followups.count_documents({
            "doctor_id": doctor_id,
            "followup_date": {"$lte": datetime.now() + timedelta(days=7)},
            "status": "pending"
        })
        
        overdue_count = db.followups.count_documents({
            "doctor_id": doctor_id,
            "followup_date": {"$lt": datetime.now()},
            "status": "pending"
        })
        
        total_followups = sum(status_counts.values())
        success_rate = (status_counts.get("completed", 0) / total_followups * 100) if total_followups > 0 else 0
        
        return {
            "total_followups": total_followups,
            "status_breakdown": status_counts,
            "upcoming_followups": upcoming_count,
            "overdue_followups": overdue_count,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"Error getting followup stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
