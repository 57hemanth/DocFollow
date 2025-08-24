"""
Portia tools for WhatsApp messaging through Twilio
"""

from typing import Annotated
from portia import tool
from backend.services.whatsapp_service import whatsapp_service
import asyncio
import logging

logger = logging.getLogger(__name__)

@tool
def send_whatsapp_message(
    patient_phone: Annotated[str, "The patient's phone number in E.164 format (e.g., +1234567890)"],
    message: Annotated[str, "The message content to send to the patient"]
) -> str:
    """
    Sends a WhatsApp message to a patient's phone number using Twilio.
    
    This tool integrates with the existing WhatsApp service to send messages
    for patient follow-ups, reminders, and other communications.
    
    Args:
        patient_phone: Phone number in E.164 format (e.g., +1234567890)
        message: The message content to send
        
    Returns:
        str: Success message with message SID or error description
    """
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            whatsapp_service.send_message(patient_phone, message)
        )
        
        loop.close()
        
        if result.get("success"):
            return f"✅ WhatsApp message sent successfully! Message SID: {result.get('message_sid')}"
        else:
            return f"❌ Failed to send WhatsApp message: {result.get('error')}"
            
    except Exception as e:
        logger.error(f"Error in send_whatsapp_message tool: {str(e)}")
        return f"❌ Error sending WhatsApp message: {str(e)}"

@tool
def send_follow_up_reminder(
    patient_phone: Annotated[str, "The patient's phone number in E.164 format"],
    patient_name: Annotated[str, "The patient's full name"],
    doctor_name: Annotated[str, "The doctor's name"],
    follow_up_date: Annotated[str, "The follow-up appointment date and time"]
) -> str:
    """
    Sends a structured follow-up reminder message to a patient via WhatsApp.
    
    This tool creates a professional, friendly reminder message that includes
    instructions for the patient to share updates, test reports, and photos.
    
    Args:
        patient_phone: Phone number in E.164 format
        patient_name: Patient's full name for personalization
        doctor_name: Doctor's name for the clinic identification
        follow_up_date: Date and time of the follow-up appointment
        
    Returns:
        str: Success message with details or error description
    """
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            whatsapp_service.send_follow_up_reminder(
                patient_phone, patient_name, doctor_name, follow_up_date
            )
        )
        
        loop.close()
        
        if result.get("success"):
            return f"✅ Follow-up reminder sent to {patient_name} successfully! Message SID: {result.get('message_sid')}"
        else:
            return f"❌ Failed to send follow-up reminder to {patient_name}: {result.get('error')}"
            
    except Exception as e:
        logger.error(f"Error in send_follow_up_reminder tool: {str(e)}")
        return f"❌ Error sending follow-up reminder: {str(e)}"


@tool
def get_whatsapp_sandbox_info() -> str:
    """
    Retrieves the Twilio WhatsApp Sandbox setup instructions.
    
    This tool provides the necessary information for patients and doctors
    to join the Twilio WhatsApp Sandbox for testing purposes.
    
    Returns:
        str: Formatted instructions for joining the WhatsApp sandbox
    """
    try:
        sandbox_info = whatsapp_service.get_sandbox_instructions()
        
        instructions = f"""
📱 **Twilio WhatsApp Sandbox Setup Instructions**

**Sandbox Number:** {sandbox_info['sandbox_number']}
**Join Code:** {sandbox_info['join_code']}

**Setup Steps:**
"""
        for instruction in sandbox_info['instructions']:
            instructions += f"\n{instruction}"
        
        instructions += f"\n\n⚠️ **Note:** {sandbox_info['note']}"
        
        return instructions
        
    except Exception as e:
        logger.error(f"Error getting sandbox info: {str(e)}")
        return f"❌ Error retrieving sandbox information: {str(e)}"

