"""
Message Analysis Agent for PingDoc - Analyzes patient responses and medical data
"""

from portia import Portia, Config, tool, PlanBuilder
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from backend.database import db
from backend.models.patients import Patient
from backend.models.followups import Followup
from .whatsapp_tools import send_whatsapp_message
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from bson import ObjectId

logger = logging.getLogger(__name__)

@tool
def extract_medical_data(
    patient_message: str,
    patient_history: str = ""
) -> str:
    """
    Extract and structure medical information from patient messages or reports.
    
    Args:
        patient_message: The patient's message, report, or image description
        patient_history: Previous medical history for context
        
    Returns:
        str: JSON string containing structured medical data
    """
    # This tool will be used by the AI to extract structured data
    return f"Analyzing message: '{patient_message}' with history: '{patient_history}'"

@tool 
def generate_doctor_summary(
    extracted_data: str,
    patient_name: str,
    original_condition: str
) -> str:
    """
    Generate a summary for the doctor based on extracted patient data.
    
    Args:
        extracted_data: Previously extracted medical data
        patient_name: Patient's name
        original_condition: Original diagnosis/condition
        
    Returns:
        str: Doctor-friendly summary of patient update
    """
    return f"Doctor summary for {patient_name} with condition {original_condition} based on: {extracted_data}"

@tool
def generate_patient_response(
    doctor_notes: str,
    patient_name: str,
    is_positive_update: bool = True
) -> str:
    """
    Generate a patient-friendly response message based on doctor's notes.
    
    Args:
        doctor_notes: Doctor's assessment and instructions
        patient_name: Patient's name for personalization
        is_positive_update: Whether the update is positive or needs attention
        
    Returns:
        str: Patient-friendly response message
    """
    tone = "encouraging" if is_positive_update else "concerned but supportive"
    return f"Generating {tone} response for {patient_name} based on: {doctor_notes}"

class MessageAnalysisAgent:
    """
    AI agent responsible for analyzing patient messages, extracting medical data,
    and generating appropriate responses for both doctors and patients.
    """
    
    def __init__(self):
        """Initialize the Message Analysis Agent with Portia configuration"""
        try:
            # Define tools list
            tools = [
                extract_medical_data(), 
                generate_doctor_summary(), 
                generate_patient_response(), 
                send_whatsapp_message()
            ]
            
            # Configure Portia based on available API keys
            if PORTIA_LLM_PROVIDER == "google" and GOOGLE_API_KEY:
                config = Config.from_default(llm_provider="google")
            elif OPENAI_API_KEY:
                config = Config.from_default(llm_provider="openai")
            else:
                logger.warning("No valid LLM provider configured. Message analysis agent may not work properly.")
                config = Config.from_default(llm_provider="google")  # Fallback
            
            # Initialize Portia with tools
            self.portia = Portia(config=config, tools=tools)
            self.db = db
            
            logger.info("Message Analysis Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Message Analysis Agent: {str(e)}")
            raise
    
    def analyze_patient_message(self, patient_id: str, doctor_id: str, message_content: str, image_urls: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a patient's message/update and extract relevant medical information.
        
        Args:
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            message_content: Patient's text message
            image_urls: List of image URLs if patient sent photos
            
        Returns:
            Dict containing analysis results and extracted data
        """
        try:
            patient = self.db.patients.find_one({"_id": ObjectId(patient_id), "doctor_id": ObjectId(doctor_id)})
            if not patient:
                return {"success": False, "error": "Patient not found"}

            analysis_instruction = f"""
            You are a medical data analysis agent. Analyze the following message from a patient named {patient['name']} and extract relevant medical data.
            The patient's message is: "{message_content}"
            If there are image URLs provided, take them into account: {image_urls}

            Please extract the data and provide a summary for the doctor. Then, draft a preliminary response to the patient acknowledging their message.
            If the patient's condition seems abnormal or urgent, your drafted response should suggest booking an appointment.
            Return the extracted data, the summary for the doctor, and the drafted patient message.
            """
            
            plan_run = self.portia.run(analysis_instruction)
            
            # For now, we will assume the output is a string that needs parsing.
            # A more robust solution would be to prompt for JSON.
            output = plan_run.output if hasattr(plan_run, 'output') else str(plan_run)

            followup_record = {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "original_data": {"message": message_content, "images": image_urls},
                "extracted_data": {"raw_analysis": output},
                "ai_draft_message": output, # Using the full output as the draft for now
                "doctor_decision": "pending_review",
                "final_message_sent": False,
                "created_at": datetime.now()
            }
            result = self.db.followups.insert_one(followup_record)
            
            return {
                "success": True, 
                "followup_id": str(result.inserted_id),
                "message": "Patient message analyzed, pending doctor review."
            }

        except Exception as e:
            logger.error(f"Error analyzing patient message: {str(e)}")
            return {"success": False, "error": str(e)}

    def doctor_decision(self, followup_id: str, decision: str, custom_message: str = None) -> Dict[str, Any]:
        """
        Process the doctor's decision on a followup.
        
        Args:
            followup_id: The ID of the followup to update
            decision: The doctor's decision ('approve', 'edit', 'custom')
            custom_message: The custom message to send if the decision is 'edit' or 'custom'
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            followup = self.db.followups.find_one({"_id": ObjectId(followup_id)})
            if not followup:
                return {"success": False, "error": "Followup not found"}

            patient = self.db.patients.find_one({"_id": ObjectId(followup['patient_id'])})
            if not patient:
                return {"success": False, "error": "Patient not found"}

            message_to_send = ""
            if decision == 'approve':
                message_to_send = followup['ai_draft_message']
            elif decision in ['edit', 'custom']:
                if not custom_message:
                    return {"success": False, "error": "Custom message is required for 'edit' or 'custom' decisions."}
                message_to_send = custom_message
            else:
                return {"success": False, "error": "Invalid decision."}

            prompt = f"Send the following WhatsApp message to the patient named {patient['name']} at the phone number {patient['phone']}: '{message_to_send}'"
            self.portia.run(prompt)

            self.db.followups.update_one(
                {"_id": ObjectId(followup_id)},
                {"$set": {
                    "doctor_decision": decision,
                    "final_message_sent": True,
                    "final_message": message_to_send
                }}
            )

            if "appointment" in message_to_send.lower():
                # Here you would trigger the Appointment Booking Agent
                pass

            return {"success": True, "message": "Doctor's decision processed and message sent."}

        except Exception as e:
            logger.error(f"Error processing doctor's decision: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance will be created by AgentRegistry  
message_analysis_agent = None
