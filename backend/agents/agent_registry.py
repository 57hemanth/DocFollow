"""
Agent Registry for DocFollow - Central management of all AI agents
"""

from typing import Dict, Any, Optional
from portia import Portia, Config, DefaultToolRegistry
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from .follow_up_agent import FollowUpAgent
from .message_analysis_agent import MessageAnalysisAgent
from .appointment_agent import AppointmentAgent
from .whatsapp_tools import send_whatsapp_message
from backend.database import db
import logging
import asyncio
from pydantic import BaseModel, Field

# Define the schema for the custom tool, as required by the Portia Tool spec
class SendWhatsAppMessageSchema(BaseModel):
    """Input schema for the send_whatsapp_message tool."""
    patient_phone: str = Field(..., description="The patient's phone number in E.164 format (e.g., +1234567890)")
    message: str = Field(..., description="The message content to send to the patient")
    followup_id: Optional[str] = Field(None, description="The ID of the followup to associate the message with")

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Central registry for managing all AI agents in the DocFollow system.
    Provides a single interface for accessing and coordinating different agents.
    """
    
    def __init__(self):
        """Initialize the agent registry with all available agents"""
        self._agents = {}
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize all agents in the registry
        
        Returns:
            bool: True if all agents initialized successfully
        """
        if self._initialized:
            logger.info("Agent registry already initialized")
            return True
        
        try:
            logger.info("Initializing AI agents...")
            
            # Configure Portia based on available API keys
            if PORTIA_LLM_PROVIDER == "google" and GOOGLE_API_KEY:
                config = Config.from_default(llm_provider="google")
            elif OPENAI_API_KEY:
                config = Config.from_default(llm_provider="openai")
            else:
                logger.warning("No valid LLM provider configured. Agents may not work properly.")
                config = Config.from_default(llm_provider="google")  # Fallback

            # Initialize Follow-up Agent
            try:
                self._agents['follow_up'] = FollowUpAgent()
                logger.info("✅ Follow-up Agent initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Follow-up Agent: {str(e)}")
                return False
            
            # Initialize Message Analysis Agent
            try:
                self._agents['message_analysis'] = MessageAnalysisAgent()
                logger.info("✅ Message Analysis Agent initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Message Analysis Agent: {str(e)}")
                return False
            
            # Initialize Appointment Agent
            try:
                logger.info("Initializing Appointment Agent...")
                logger.info("Creating tool registry for Portia Cloud tools...")
                # Use DefaultToolRegistry which includes cloud tools if an API key is available
                tools = DefaultToolRegistry(config)
                
                # Manually set all required attributes for the custom tool to make it valid
                send_whatsapp_message.id = "send_whatsapp_message"
                send_whatsapp_message.name = "send_whatsapp_message"
                send_whatsapp_message.description = "Sends a WhatsApp message to a patient's phone number."
                send_whatsapp_message.args_schema = SendWhatsAppMessageSchema
                send_whatsapp_message.output_schema = str
                
                tools += [send_whatsapp_message]
                logger.info("✅ Tool registry created successfully.")
                
                logger.info("Initializing Portia instance...")
                # Run the synchronous Portia constructor in a separate thread
                portia_instance = await asyncio.to_thread(Portia, config=config, tools=tools)
                logger.info("✅ Portia instance initialized successfully.")
                
                # Create the AppointmentAgent with the Portia instance
                self._agents['appointment'] = AppointmentAgent(portia_instance)
                logger.info("✅ Appointment Agent initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Appointment Agent: {str(e)}", exc_info=True)
                return False
            
            self._initialized = True
            logger.info("🎉 All AI agents initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent registry: {str(e)}")
            return False
    
    def get_follow_up_agent(self) -> Optional[FollowUpAgent]:
        """
        Get the Follow-up Agent instance
        
        Returns:
            FollowUpAgent or None if not initialized
        """
        if not self._initialized:
            logger.warning("Agent registry not initialized. Call initialize() first.")
            return None
        
        return self._agents.get('follow_up')
    
    def get_message_analysis_agent(self) -> Optional[MessageAnalysisAgent]:
        """
        Get the Message Analysis Agent instance
        
        Returns:
            MessageAnalysisAgent or None if not initialized
        """
        if not self._initialized:
            logger.warning("Agent registry not initialized. Call initialize() first.")
            return None
        
        return self._agents.get('message_analysis')
    
    def get_appointment_agent(self) -> Optional[AppointmentAgent]:
        """
        Get the Appointment Agent instance
        
        Returns:
            AppointmentAgent or None if not initialized
        """
        if not self._initialized:
            logger.warning("Agent registry not initialized. Call initialize() first.")
            return None
        
        return self._agents.get('appointment')
    
    def is_initialized(self) -> bool:
        """Check if the registry is initialized"""
        return self._initialized
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the status of all agents
        
        Returns:
            Dict containing status information for all agents
        """
        return {
            "initialized": self._initialized,
            "agents": {
                "follow_up": "available" if self._agents.get('follow_up') else "not_available",
                "message_analysis": "available" if self._agents.get('message_analysis') else "not_available",
                "appointment": "available" if self._agents.get('appointment') else "not_available"
            },
            "total_agents": len(self._agents)
        }
    
    async def process_patient_message(self, patient_id: str, doctor_id: str, message_content: str, image_urls: list = None) -> Dict[str, Any]:
        """
        Process an incoming patient message through the appropriate agent workflow
        
        Args:
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            message_content: Patient's message content
            image_urls: List of image URLs if provided
            
        Returns:
            Dict containing processing results
        """
        if not self._initialized:
            return {"success": False, "error": "Agent registry not initialized"}
        
        message_agent = self.get_message_analysis_agent()
        if not message_agent:
            return {"success": False, "error": "Message analysis agent not available"}
        
        try:
            return await message_agent.analyze_patient_message(
                patient_id, doctor_id, message_content, image_urls
            )
        except Exception as e:
            logger.error(f"Error processing patient message: {str(e)}")
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
        if not self._initialized:
            return {"success": False, "error": "Agent registry not initialized"}
        
        message_agent = self.get_message_analysis_agent()
        if not message_agent:
            return {"success": False, "error": "Message analysis agent not available"}
        
        try:
            return await message_agent.doctor_decision(followup_id, decision, custom_message)
        except Exception as e:
            logger.error(f"Error processing doctor's decision: {str(e)}")
            return {"success": False, "error": str(e)}

    async def send_follow_up_reminder(self, patient_id: str, doctor_id: str, follow_up_date: str) -> Dict[str, Any]:
        """
        Send a follow-up reminder to a patient
        
        Args:
            patient_id: Patient's database ID
            doctor_id: Doctor's database ID
            follow_up_date: The date of the follow-up
            
        Returns:
            Dict containing the result of the operation
        """
        if not self._initialized:
            return {"success": False, "error": "Agent registry not initialized"}
        
        follow_up_agent = self.get_follow_up_agent()
        if not follow_up_agent:
            return {"success": False, "error": "Follow-up agent not available"}
        
        try:
            # This is a placeholder for a more complex implementation
            return await follow_up_agent.trigger_follow_up(patient_id, doctor_id)
        except Exception as e:
            logger.error(f"Error sending follow-up reminder: {str(e)}")
            return {"success": False, "error": str(e)}

    async def approve_and_send_response(self, followup_id: str, final_message: str, doctor_id: str) -> Dict[str, Any]:
        """
        Approve and send a response message to a patient
        
        Args:
            followup_id: The ID of the followup
            final_message: The final message to be sent
            doctor_id: The ID of the doctor
            
        Returns:
            Dict containing the result of the operation
        """
        if not self._initialized:
            return {"success": False, "error": "Agent registry not initialized"}
        
        message_agent = self.get_message_analysis_agent()
        if not message_agent:
            return {"success": False, "error": "Message analysis agent not available"}
        
        try:
            return await message_agent.doctor_decision(followup_id, 'approve', final_message)
        except Exception as e:
            logger.error(f"Error approving and sending response: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_pending_doctor_reviews(self, doctor_id: str) -> Dict[str, Any]:
        """
        Get all followups pending doctor review
        
        Args:
            doctor_id: The ID of the doctor
            
        Returns:
            Dict containing the list of pending reviews
        """
        if not self._initialized:
            return {"success": False, "error": "Agent registry not initialized"}
        
        try:
            pending_reviews = list(db.followups.find({"doctor_id": doctor_id, "doctor_decision": "pending_review"}))
            return {"success": True, "reviews": pending_reviews}
        except Exception as e:
            logger.error(f"Error getting pending reviews: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance - will be initialized when the server starts
agent_registry = AgentRegistry()
