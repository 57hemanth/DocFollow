"""
Follow-up Agent for PingDoc - Handles automated patient follow-up workflows
"""

from portia import Portia, Config, PlanBuilder
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from backend.database import db
from backend.models.patients import Patient
from backend.schemas.followups import Message
from .whatsapp_tools import send_whatsapp_message
import logging
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
import asyncio

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
    
    async def trigger_initial_followup(self, patient_id: str, doctor_id: str, followup_id: str):
        """
        Generates and sends the initial follow-up message using the AI agent.
        """
        patient = self.db.patients.find_one({"_id": ObjectId(patient_id)})
        doctor = self.db.doctors.find_one({"_id": ObjectId(doctor_id)})

        if not patient or not doctor:
            raise ValueError("Patient or Doctor not found")

        diagnosis_instructions = {
            "sugar": "Ask the patient to send their past 3 days' sugar level readings.",
            "fever": "Ask for the temperature readings of the patient.",
            "default": "Draft a general follow-up message asking the patient about their well-being."
        }
        instruction = diagnosis_instructions.get(patient.get('disease', '').lower(), diagnosis_instructions['default'])

        prompt = f"""
        You are a medical assistant for Dr. {doctor['name']}.
        Your task is to send a follow-up message to a patient named {patient['name']} via WhatsApp.
        The patient's phone number is {patient['phone']}.
        The followup ID is {followup_id}. You must use this ID when sending the message.
        
        Based on the patient's condition ({patient.get('disease', 'N/A')}), here is your instruction: "{instruction}"

        Please compose a friendly, professional, and clear WhatsApp message based on this instruction, and then send it to the patient's phone number using the available tool.
        """
        
        # Run Portia agent to execute the plan
        await asyncio.to_thread(self.portia.run, prompt)

# Global instance will be created by AgentRegistry
follow_up_agent = None
