"""
Follow-up Agent for PingDoc - Handles automated patient follow-up workflows
"""

from portia import Portia, Config, PlanBuilder
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from backend.database import db
from backend.models.patients import Patient
from backend.models.followups import Followup
from .whatsapp_tools import send_whatsapp_message
import logging
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId

logger = logging.getLogger(__name__)

class FollowUpAgent:
    """
    AI agent responsible for managing patient follow-up workflows including:
    - Sending automated follow-up reminders via WhatsApp
    - Generating personalized follow-up messages
    - Scheduling and tracking follow-up communications
    """
    
    def __init__(self):
        """Initialize the Follow-up Agent with Portia configuration"""
        try:
            # Define tools list - create instances
            tools = [send_whatsapp_message()]
            
            # Configure Portia based on available API keys
            if PORTIA_LLM_PROVIDER == "google" and GOOGLE_API_KEY:
                config = Config.from_default(llm_provider="google")
            elif OPENAI_API_KEY:
                config = Config.from_default(llm_provider="openai")
            else:
                logger.warning("No valid LLM provider configured. Follow-up agent may not work properly.")
                config = Config.from_default(llm_provider="google")  # Fallback
            
            # Initialize Portia with tools directly
            self.portia = Portia(config=config, tools=tools)
            self.db = db
            
            logger.info("Follow-up Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Follow-up Agent: {str(e)}")
            raise
    
    def trigger_follow_up(self, patient_id: str, doctor_id: str) -> Dict[str, Any]:
        """
        Trigger a follow-up for a patient based on their diagnosis.
        
        Args:
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            
        Returns:
            Dict containing the result of the follow-up attempt
        """
        try:
            patient = self.db.patients.find_one({"_id": ObjectId(patient_id), "doctor_id": doctor_id})
            if not patient:
                return {"success": False, "error": "Patient not found"}

            doctor = self.db.doctors.find_one({"_id": ObjectId(doctor_id)})
            if not doctor:
                return {"success": False, "error": "Doctor not found"}

            # Define diagnosis-based instructions
            diagnosis_instructions = {
                "sugar": "Ask the patient to send their past 3 days' sugar level readings.",
                "fever": "Ask for the temperature readings of the patient.",
                "default": "Draft a general follow-up message asking the patient about their well-being."
            }

            instruction = diagnosis_instructions.get(patient.get('diagnosis', '').lower(), diagnosis_instructions['default'])

            prompt = f"""
            You are a medical assistant for Dr. {doctor['name']}.
            Your task is to send a follow-up message to a patient named {patient['name']} via WhatsApp.
            The patient's phone number is {patient['phone']}.
            
            Based on the patient's condition, here is the instruction for the message: "{instruction}"

            Please compose a friendly, professional, and clear WhatsApp message based on this instruction, and then send it to the patient's phone number.
            """

            plan_run = self.portia.run(prompt)
            
            follow_up_record = {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "ai_draft_message": f"Follow-up for {patient.get('diagnosis', 'N/A')} triggered.",
                "doctor_decision": "automated",
                "final_message_sent": True,
                "created_at": datetime.now()
            }
            self.db.followups.insert_one(follow_up_record)
            
            return {
                "success": True, 
                "message": f"Follow-up triggered for {patient['name']}",
                "plan_run_id": plan_run.id if hasattr(plan_run, 'id') else None
            }

        except Exception as e:
            logger.error(f"Error triggering follow-up: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance will be created by AgentRegistry
follow_up_agent = None
