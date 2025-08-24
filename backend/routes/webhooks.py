from fastapi import APIRouter, Request, Form, HTTPException
from backend.database import db
from backend.services.whatsapp_service import whatsapp_service
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
    Handle incoming WhatsApp messages from Twilio
    
    This webhook receives messages sent by patients to the WhatsApp Sandbox number
    """
    try:
        logger.info(f"Received WhatsApp message from {From}: {Body}")
        
        form_data = await request.form()
        
        patient_phone = From.replace("whatsapp:", "")
        patient = db.patients.find_one({"phone": patient_phone})
        
        if not patient:
            logger.warning(f"No patient found with phone number: {patient_phone}")
            return {"status": "success", "message": "Patient not found"}
        
        from backend.agents import agent_registry
        message_analysis_agent = agent_registry.get_message_analysis_agent()
        if not message_analysis_agent:
            logger.error("Message Analysis Agent not available")
            raise HTTPException(status_code=500, detail="Message Analysis Agent not available")

        media_items = []
        if NumMedia > 0:
            for i in range(NumMedia):
                media_url = form_data.get(f"MediaUrl{i}")
                content_type = form_data.get(f"MediaContentType{i}")
                if media_url:
                    media_items.append({"url": media_url, "content_type": content_type})
        
        result = await message_analysis_agent.analyze_patient_message(
            patient_id=str(patient["_id"]),
            doctor_id=patient["doctor_id"],
            message_content=Body,
            media_items=media_items
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process message"))

        return {
            "status": "success", 
            "message": "Message processed and sent for analysis",
            "followup_id": result.get("followup_id")
        }
        
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
