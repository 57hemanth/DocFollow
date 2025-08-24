from fastapi import APIRouter, Body, HTTPException, status
from typing import List, Dict, Any, Optional
from backend.schemas.followups import Followup, FollowupCreate, FollowupUpdate
from backend.database import db
from bson import ObjectId
from backend.agents import agent_registry
from backend.services.scheduler_service import scheduler_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/followups", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_followup(followup_data: FollowupCreate):
    """
    Trigger a new follow-up, create the document, and have the agent send the initial message.
    """
    try:
        # 1. Create the preliminary followup document
        if followup_data.followup_date:
            new_followup = Followup(
                patient_id=followup_data.patient_id,
                doctor_id=followup_data.doctor_id,
                raw_data=followup_data.raw_data,
                status="scheduled", # Temporary status
            )
        else:
            new_followup = Followup(
                patient_id=followup_data.patient_id,
                doctor_id=followup_data.doctor_id,
                raw_data=followup_data.raw_data,
                status="creating", # Temporary status
            )

        result = db.followups.insert_one(new_followup.dict(by_alias=True, exclude={"id"}))
        followup_id = str(result.inserted_id)

        # 2. Trigger agent to generate and send initial message
        if followup_data.followup_date:
            await scheduler_service.schedule_follow_up_reminder(
                remainder_id=followup_id,
                patient_id=followup_data.patient_id,
                doctor_id=followup_data.doctor_id,
                followup_datetime=followup_data.followup_date,
            )
        else:
            follow_up_agent = agent_registry.get_follow_up_agent()
            await follow_up_agent.trigger_follow_up(
                patient_id=followup_data.patient_id,
                doctor_id=followup_data.doctor_id,
                followup_id=followup_id,
                raw_data=followup_data.raw_data
            )

        return {
            "success": True,
            "followup_id": followup_id,
            "message": "Follow-up triggered successfully."
        }
    except Exception as e:
        logger.error(f"Error creating followup: {e}")
        # Clean up preliminary document if agent fails
        if 'followup_id' in locals():
            db.followups.delete_one({"_id": ObjectId(followup_id)})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followups", response_model=List[Followup])
def get_followups(doctor_id: str, status: Optional[str] = None):
    """Get all follow-ups for a doctor, optionally filtered by status"""
    try:
        query = {"doctor_id": doctor_id}
        if status:
            query["status"] = status
            
        followups = list(db.followups.find(query).sort("updated_at", -1))
        return followups
    except Exception as e:
        logger.error(f"Error getting followups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followups/{followup_id}", response_model=Followup)
def get_followup(followup_id: str, doctor_id: str):
    """Get a specific followup by ID"""
    try:
        followup = db.followups.find_one({"_id": ObjectId(followup_id), "doctor_id": doctor_id})
        
        if not followup:
            raise HTTPException(status_code=404, detail="Followup not found")
        
        return Followup(**followup)
    except Exception as e:
        logger.error(f"Error getting followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/followups/{followup_id}", response_model=Dict[str, Any])
async def update_followup(followup_id: str, update_data: FollowupUpdate):
    """
    Update a followup document.
    """
    try:
        update_fields = update_data.dict(exclude_unset=True)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        result = db.followups.update_one(
            {"_id": ObjectId(followup_id)},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Followup not found")

        return {"success": True, "message": "Follow-up updated successfully."}
    except Exception as e:
        logger.error(f"Error updating followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/followups/{followup_id}/send-message", response_model=Dict[str, Any])
async def send_doctor_message(followup_id: str, doctor_id: str, message_content: str = Body(..., embed=True)):
    """
    Send a message from the doctor to the patient and update the follow-up.
    """
    try:
        # This is a placeholder for the agent call to send the message
        # You would replace this with your actual WhatsApp sending logic
        print(f"Sending message to patient for followup {followup_id}: {message_content}")

        # Update history
        new_message = {
            "sender": "doctor",
            "content": message_content,
            "timestamp": datetime.now()
        }

        result = db.followups.update_one(
            {"_id": ObjectId(followup_id), "doctor_id": doctor_id},
            {
                "$push": {"history": new_message},
                "$set": {"status": "closed", "updated_at": datetime.now()} # Or another appropriate status
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Followup not found or doctor mismatch")

        return {"success": True, "message": "Message sent and followup updated."}
    except Exception as e:
        logger.error(f"Error sending doctor message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/followups/{followup_id}/send-ai-draft", response_model=Dict[str, Any])
async def send_ai_draft(followup_id: str, doctor_id: str):
    """
    Send the AI-drafted message to the patient via WhatsApp.
    """
    try:
        followup = db.followups.find_one({"_id": ObjectId(followup_id), "doctor_id": doctor_id})
        if not followup:
            raise HTTPException(status_code=404, detail="Followup not found")

        ai_draft = followup.get("ai_draft_message")
        if not ai_draft:
            raise HTTPException(status_code=400, detail="No AI draft message to send")

        patient = db.patients.find_one({"_id": ObjectId(followup["patient_id"])})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        message_analysis_agent = agent_registry.get_message_analysis_agent()
        
        # Using the agent to send the message
        await message_analysis_agent.doctor_decision(
            followup_id=followup_id,
            decision='approve'
        )

        return {"success": True, "message": "AI draft message sent successfully."}
    except Exception as e:
        logger.error(f"Error sending AI draft message: {e}")
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
        
        total_followups = sum(status_counts.values())
        
        return {
            "total_followups": total_followups,
            "status_breakdown": status_counts,
        }
    except Exception as e:
        logger.error(f"Error getting followup stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
