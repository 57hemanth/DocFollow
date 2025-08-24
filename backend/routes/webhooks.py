from fastapi import APIRouter, Request, Form, HTTPException
from backend.database import db
from backend.services.whatsapp_service import whatsapp_service
from typing import Optional
import logging
from datetime import datetime
from backend.agents import agent_registry

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_latest_followup_for_patient(patient_id: str):
    """
    Find the most recent followup for a patient that is waiting for a response
    or is currently being reviewed by the doctor.
    """
    return db.followups.find_one(
        {
            "patient_id": patient_id,
            "status": {"$in": ["waiting_for_patient", "waiting_for_doctor"]}
        },
        sort=[("created_at", -1)]
    )

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    NumMedia: int = Form(0),
):
    """
    Handle incoming WhatsApp messages from Twilio, update the follow-up,
    and trigger the analysis agent.
    """
    try:
        logger.info(f"Received WhatsApp message from {From}: {Body}")
        
        form_data = await request.form()
        
        patient_phone = From.replace("whatsapp:", "")
        patient = db.patients.find_one({"phone": patient_phone})
        
        if not patient:
            logger.warning(f"No patient found with phone number: {patient_phone}")
            return {"status": "success", "message": "Patient not found."}

        patient_id = str(patient["_id"])
        followup = await get_latest_followup_for_patient(patient_id)

        if not followup:
            logger.warning(f"No active followup found for patient {patient_id}")
            return {"status": "success", "message": "No active followup."}

        # 1. Update Follow-up History and Media
        new_message = {
            "sender": "patient",
            "content": Body,
            "timestamp": datetime.now()
        }
        
        media_urls = [form_data.get(f"MediaUrl{i}") for i in range(NumMedia) if form_data.get(f"MediaUrl{i}")]
        
        update_query = {
            "$push": {"history": new_message},
            "$set": {
                "status": "waiting_for_doctor",
                "updated_at": datetime.now()
            }
        }
        if media_urls:
            update_query["$addToSet"] = {"original_data": {"$each": media_urls}}

        update_result = db.followups.update_one({"_id": followup["_id"]}, update_query)
        
        if update_result.matched_count == 0:
            logger.error(f"Failed to update followup {followup['_id']} for patient {patient_id}")
            # Potentially retry or handle error
            return {"status": "error", "message": "Failed to update followup."}

        # 2. Trigger asynchronous agent processing
        message_analysis_agent = agent_registry.get_message_analysis_agent()
        if message_analysis_agent:
            await message_analysis_agent.process_patient_response(
                followup_id=str(followup["_id"]),
                message_content=Body,
                media_urls=media_urls
            )

        return {"status": "success", "message": "Patient response received and processing initiated."}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    Webhook verification endpoint for Twilio
    """
    return {"status": "WhatsApp webhook endpoint active"}

@router.post("/webhooks/whatsapp/test")
async def test_whatsapp_send():
    """
    Test endpoint to send a WhatsApp message
    """
    if not whatsapp_service.is_configured():
        raise HTTPException(status_code=500, detail="WhatsApp service not configured")
    
    # This is for testing - replace with actual phone number
    test_number = "+1234567890"  # Replace with your test number
    test_message = "Hello! This is a test message. WhatsApp integration is working! 🎉"
    
    result = await whatsapp_service.send_message(test_number, test_message)
    
    if result["success"]:
        return {"status": "success", "message": "Test message sent", "result": result}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {result['error']}")
