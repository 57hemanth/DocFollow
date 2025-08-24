"""
Agent routes for PingDoc - API endpoints for AI agent functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from backend.agents import agent_registry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Pydantic models for request/response
class FollowUpRequest(BaseModel):
    patient_id: str
    doctor_id: str
    follow_up_date: str

class CustomMessageRequest(BaseModel):
    patient_id: str
    doctor_id: str
    message: str

class PatientMessageRequest(BaseModel):
    patient_id: str
    doctor_id: str
    message_content: str
    image_urls: Optional[List[str]] = None

class ApproveResponseRequest(BaseModel):
    followup_id: str
    final_message: str
    doctor_id: str

class BatchFollowUpRequest(BaseModel):
    doctor_id: str
    days_ahead: int = 1

@router.get("/status")
async def get_agent_status():
    """Get the status of all AI agents"""
    try:
        status = agent_registry.get_agent_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_agents():
    """Initialize all AI agents"""
    try:
        success = agent_registry.initialize()
        if success:
            return {
                "success": True,
                "message": "All agents initialized successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize agents")
    except Exception as e:
        logger.error(f"Error initializing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/follow-up/send")
async def send_follow_up_reminder(request: FollowUpRequest):
    """Send an automated follow-up reminder to a patient"""
    try:
        result = await agent_registry.send_follow_up_reminder(
            request.patient_id,
            request.doctor_id,
            request.follow_up_date
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending follow-up reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/follow-up/custom")
async def send_custom_follow_up(request: CustomMessageRequest):
    """Send a custom follow-up message to a patient"""
    try:
        result = await agent_registry.send_custom_follow_up(
            request.patient_id,
            request.doctor_id,
            request.message
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending custom follow-up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/analyze")
async def analyze_patient_message(request: PatientMessageRequest):
    """Analyze an incoming patient message and generate response draft"""
    try:
        result = await agent_registry.process_patient_message(
            request.patient_id,
            request.doctor_id,
            request.message_content,
            request.image_urls
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing patient message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/approve")
async def approve_and_send_response(request: ApproveResponseRequest):
    """Approve and send a response message to patient"""
    try:
        result = await agent_registry.approve_and_send_response(
            request.followup_id,
            request.final_message,
            request.doctor_id
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving and sending response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reviews/pending/{doctor_id}")
async def get_pending_reviews(doctor_id: str):
    """Get all followups pending doctor review"""
    try:
        result = await agent_registry.get_pending_doctor_reviews(doctor_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/sandbox-info")
async def get_whatsapp_sandbox_info():
    """Get WhatsApp sandbox setup instructions"""
    try:
        follow_up_agent = agent_registry.get_follow_up_agent()
        if not follow_up_agent:
            raise HTTPException(status_code=503, detail="Follow-up agent not available")
        
        result = follow_up_agent.get_sandbox_instructions()
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sandbox info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
