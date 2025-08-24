from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from backend.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
from backend.database import db
from backend.models.followups import Message
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured. WhatsApp functionality will be disabled.")
            self.client = None
        else:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured"""
        return self.client is not None
    
    async def send_message(self, to_number: str, message: str, followup_id: Optional[str] = None) -> dict:
        """
        Send WhatsApp message via Twilio Sandbox
        
        Args:
            to_number: Phone number in format "+1234567890"
            message: Message content to send
            followup_id: Optional ID of the followup to associate the message with
            
        Returns:
            dict: Response with success status and message_sid or error
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Twilio WhatsApp not configured"
            }
        
        try:
            # Ensure the number is in WhatsApp format
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            response = self.client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=to_number
            )
            
            if followup_id:
                history_entry = Message(sender="agent", content=message)
                db.followups.update_one(
                    {"_id": followup_id},
                    {"$push": {"history": history_entry.dict()}}
                )

            logger.info(f"WhatsApp message sent successfully. SID: {response.sid}")
            return {
                "success": True,
                "message_sid": response.sid,
                "status": response.status
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def send_follow_up_reminder(self, patient_phone: str, patient_name: str, doctor_name: str, follow_up_date: str, followup_id: Optional[str] = None) -> dict:
        """
        Send a follow-up reminder message to patient
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            doctor_name: Doctor's name
            follow_up_date: Follow-up date string
            followup_id: Optional ID of the followup to associate the message with
            
        Returns:
            dict: Response with success status
        """
        message = f"""
Hello {patient_name}! 👋

This is a friendly reminder from Dr. {doctor_name}'s clinic.

📅 You have a follow-up scheduled for {follow_up_date}.

Please reply to this message with:
- Any recent test reports 📋
- Photos of affected areas 📸
- Updates on your condition 💬

We're here to help with your continued care!

Best regards,
Dr. {doctor_name}'s Team
        """.strip()
        
        return await self.send_message(patient_phone, message, followup_id=followup_id)
    
    async def send_custom_message(self, patient_phone: str, message: str, followup_id: Optional[str] = None) -> dict:
        """
        Send a custom message to patient
        
        Args:
            patient_phone: Patient's phone number
            message: Custom message content
            followup_id: Optional ID of the followup to associate the message with
            
        Returns:
            dict: Response with success status
        """
        return await self.send_message(patient_phone, message, followup_id=followup_id)
    
    def get_sandbox_instructions(self) -> dict:
        """
        Get instructions for joining Twilio WhatsApp Sandbox
        
        Returns:
            dict: Instructions for sandbox setup
        """
        return {
            "sandbox_number": "+1 415 523 8886",
            "join_code": "join firm-scale",
            "instructions": [
                "1. Save the sandbox number +1 415 523 8886 to your contacts as 'Twilio Sandbox'",
                "2. Send a WhatsApp message with 'join firm-scale' to this number",
                "3. You'll receive a confirmation message when successfully joined",
                "4. Your patients need to join the sandbox using the same process"
            ],
            "note": "This is for development/testing. In production, you'll need an approved Twilio WhatsApp Business Account."
        }

# Global instance
whatsapp_service = WhatsAppService()
