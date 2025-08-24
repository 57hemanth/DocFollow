"""
Message Analysis Agent for DocFollow - Analyzes patient responses and medical data
"""

from portia import Portia, Config, tool, PlanBuilder, LLMProvider
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from backend.database import db
from backend.models.patients import Patient
from backend.models.followups import Followup
from .whatsapp_tools import send_whatsapp_message
from backend.services.cloudinary_service import cloudinary_service
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from bson import ObjectId
import asyncio
import os
import requests
from dotenv import load_dotenv
import tempfile
import mimetypes
from PIL import Image
import easyocr
from pypdf import PdfReader

load_dotenv()

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

async def process_patient_response(followup_id: str, patient_id: str, doctor_id: str, message_content: str, media_urls: List[str]):
    """
    Asynchronously process the patient's response, extract data,
    and update the followup with an AI-drafted message.
    """
    try:
        logger.info(f"Processing response for followup_id: {followup_id}")

        agent = MessageAnalysisAgent()
        
        # Download images from twilio and upload to cloudinary
        if media_urls:
            cloudinary_urls = []
            for url in media_urls:
                content_type = "image/jpeg" 
                
                local_path = await agent._download_twilio_media(url, content_type)
                if local_path:
                    upload_result = cloudinary_service.upload_file(local_path)
                    if upload_result:
                        cloudinary_urls.append(upload_result["secure_url"])
                    
                    text = await agent._extract_text_from_media(local_path, content_type)
                    if text:
                        message_content += f"\n--- Extracted from document ---\n{text}\n--- End of document ---"

                    os.remove(local_path)
            
            if cloudinary_urls:
                db.followups.update_one(
                    {"_id": ObjectId(followup_id)},
                    {"$addToSet": {"raw_data": {"$each": cloudinary_urls}}}
                )

        # Fetch patient's name to provide context to the AI
        patient = db.patients.find_one({"_id": ObjectId(patient_id)})
        patient_name = patient.get("name", "Patient") if patient else "Patient"

        # Analyze the patient's readings to generate a draft message
        analysis_instruction = f"""
Analyze the patient's readings from the message below and determine if they are normal or abnormal.
- If the sugar level is from 0 to 140, consider it normal.
- If the sugar level is 140 or above, consider it abnormal.

Based on your analysis, generate a message for the patient.

If the readings are normal, the message should be reassuring and advise the patient to continue their medication. For example: "Thank you for sharing the readings. Your readings are normal, please continue the medication."

If the readings are abnormal, the message should be alarming and advise the patient to visit the doctor immediately. For example: "Thank you for sharing the readings. Your readings are abnormal, please visit me immediately for the checkup."

The response should only be the message to the patient, without any preamble.

Patient's name: {patient_name}
Patient's message: "{message_content}"
"""
        config = Config.from_default(llm_provider=LLMProvider.GOOGLE)

        portia = Portia(config=config)

        plan_run = await asyncio.to_thread(portia.run, analysis_instruction)
        
        dump = plan_run.model_dump()
        ai_draft = ""
        if "outputs" in dump and dump["outputs"]:
            final_output = dump["outputs"].get("final_output")
            if final_output and "value" in final_output:
                ai_draft = final_output["value"]

        note = "Patient response has been processed by the agent."
        extracted_data = {
            "text": message_content,
            "media_count": len(media_urls)
        }

        db.followups.update_one(
            {"_id": ObjectId(followup_id)},
            {
                "$set": {
                    "extracted_data": extracted_data,
                    "ai_draft_message": ai_draft,
                    "note": note,
                }
            }
        )
        logger.info(f"Successfully processed and updated followup {followup_id}")
    except Exception as e:
        logger.error(f"Error processing patient response for followup {followup_id}: {e}")
        db.followups.update_one(
            {"_id": ObjectId(followup_id)},
            {"$set": {"note": f"Agent processing failed: {e}"}}
        )

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
            self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.ocr_reader = easyocr.Reader(['en'])
            
            logger.info("Message Analysis Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Message Analysis Agent: {str(e)}")
            raise

    async def _download_twilio_media(self, media_url: str, content_type: str) -> Optional[str]:
        """Download media from a Twilio URL."""
        try:
            response = requests.get(
                media_url,
                auth=(self.twilio_account_sid, self.twilio_auth_token)
            )
            response.raise_for_status()
            
            extension = mimetypes.guess_extension(content_type) or ""
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Twilio media: {e}")
            return None

    async def _extract_text_from_media(self, file_path: str, content_type: str) -> str:
        """Extract text from an image or PDF file."""
        try:
            if content_type.startswith('image'):
                result = self.ocr_reader.readtext(file_path)
                return " ".join([text for _, text, _ in result])
            elif content_type == 'application/pdf':
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            else:
                logger.warning(f"Unsupported media type: {content_type}")
                return ""
        except Exception as e:
            logger.error(f"Failed to extract text from media: {e}")
            return ""

    async def analyze_patient_message(self, patient_id: str, doctor_id: str, message_content: str, media_items: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze a patient's message/update and extract relevant medical information.
        
        Args:
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            message_content: Patient's text message
            media_items: List of media items with url and content_type
            
        Returns:
            Dict containing analysis results and extracted data
        """
        try:
            patient = self.db.patients.find_one({"_id": ObjectId(patient_id), "doctor_id": ObjectId(doctor_id)})
            if not patient:
                return {"success": False, "error": "Patient not found"}

            # Find the most recent followup for the patient to maintain a single conversation thread
            followup = self.db.followups.find_one(
                {"patient_id": patient_id},
                sort=[("created_at", -1)]
            )

            if followup:
                followup_id = followup["_id"]
                # Keep raw_data as a simple list of URLs
                raw_data = followup.get("raw_data", [])
                # Keep extracted_data as a single string
                extracted_data = followup.get("extracted_data", "")
            else:
                followup_id = ObjectId()
                raw_data = []
                extracted_data = ""

            # Append the current message to the extracted_data string for context
            if message_content:
                extracted_data += f"\nPatient message: {message_content}\n"

            if media_items:
                for item in media_items:
                    url = item["url"]
                    content_type = item["content_type"]
                    local_path = await self._download_twilio_media(url, content_type)
                    if local_path:
                        upload_result = cloudinary_service.upload_file(local_path)
                        if upload_result:
                            raw_data.append(upload_result["secure_url"])
                        
                        text = await self._extract_text_from_media(local_path, content_type)
                        if text:
                            extracted_data += f"\n--- Extracted from document ---\n{text}\n--- End of document ---"
                        
                        os.remove(local_path)

            # Update the followup document before calling the analysis agent
            followup_update_data = {
                "raw_data": raw_data,
                "extracted_data": extracted_data,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "doctor_decision": "pending_review",
                "final_message_sent": False,
            }
            if not followup:
                followup_update_data["created_at"] = datetime.now()

            self.db.followups.update_one(
                {"_id": followup_id},
                {"$set": followup_update_data},
                upsert=True
            )

            analysis_instruction = f"""
            You are a medical data analysis agent. Analyze the following message from a patient named {patient['name']} who has a condition of {patient.get('disease', 'Not specified')}. 
            Extract relevant medical data from the following text, which includes patient messages and text extracted from documents:
            "{extracted_data}"

            Please provide a summary for the doctor. Then, draft a preliminary response to the patient acknowledging their message.
            If the patient's condition seems abnormal or urgent, your drafted response should suggest booking an appointment.
            Return the extracted data, the summary for the doctor, and the drafted patient message.
            """
            
            plan_run = await asyncio.to_thread(self.portia.run, analysis_instruction)
            
            # For now, we will assume the output is a string that needs parsing.
            # A more robust solution would be to prompt for JSON.
            output = plan_run.output if hasattr(plan_run, 'output') else str(plan_run)
            
            # Update the followup with the analysis output
            self.db.followups.update_one(
                {"_id": followup_id},
                {"$set": {
                    "extracted_data": extracted_data + f"\n\n--- AI Analysis ---\n{output}",
                    "ai_draft_message": output
                }}
            )
            
            return {
                "success": True, 
                "followup_id": str(followup_id),
                "message": "Patient message analyzed, pending doctor review."
            }

        except Exception as e:
            logger.error(f"Error analyzing patient message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def doctor_decision(self, followup_id: str, decision: str, custom_message: str = None) -> Dict[str, Any]:
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
            await asyncio.to_thread(self.portia.run, prompt)

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
