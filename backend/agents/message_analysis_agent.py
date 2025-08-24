"""
Message Analysis Agent for PingDoc - Analyzes patient responses and medical data
"""

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

class MessageAnalysisAgent:
    """
    AI agent responsible for analyzing patient messages, extracting medical data,
    and generating appropriate responses for both doctors and patients.
    """
    
    def __init__(self):
        """Initialize the Message Analysis Agent with Portia configuration"""
        try:
            # For this agent, we might not need Portia if we're just doing OCR
            self.db = db
            self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.ocr_reader = easyocr.Reader(['en'])
            
            logger.info("Message Analysis Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Message Analysis Agent: {str(e)}")
            raise

    async def _download_twilio_media(self, media_url: str) -> Optional[str]:
        """Download media from a Twilio URL."""
        try:
            response = requests.get(
                media_url,
                auth=(self.twilio_account_sid, self.twilio_auth_token)
            )
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type')
            extension = mimetypes.guess_extension(content_type) if content_type else ""
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name, content_type
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Twilio media: {e}")
            return None, None

    async def _extract_text_from_media(self, file_path: str, content_type: str) -> str:
        """Extract text from an image or PDF file."""
        try:
            if not content_type:
                return ""
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
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def process_patient_response(self, followup_id: str, message_content: str, media_urls: List[str]):
        """
        Asynchronously process the patient's response, extract data from media,
        and update the followup with an AI-drafted message.
        """
        try:
            logger.info(f"Processing response for followup_id: {followup_id}")

            extracted_texts = []
            for url in media_urls:
                local_path, content_type = await self._download_twilio_media(url)
                if local_path and content_type:
                    text = await self._extract_text_from_media(local_path, content_type)
                    if text:
                        extracted_texts.append(text)

            combined_text = message_content + "\n\n" + "\n\n".join(extracted_texts)
            
            # This is a placeholder for your actual data extraction and AI logic.
            # You would use Portia SDK or other services here.
            extracted_data = {"text": combined_text, "media_count": len(media_urls)}
            ai_draft = f"AI draft based on patient response: '{combined_text}'"
            note = "Patient response has been processed, and text has been extracted."

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

# Global instance will be created by AgentRegistry  
message_analysis_agent = None
