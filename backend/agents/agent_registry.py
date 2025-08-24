"""
Agent Registry for PingDoc - Central management of all AI agents
"""

from typing import Dict, Any, Optional
from .follow_up_agent import FollowUpAgent
from .message_analysis_agent import MessageAnalysisAgent
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Central registry for managing all AI agents in the PingDoc system.
    Provides a single interface for accessing and coordinating different agents.
    """
    
    def __init__(self):
        """Initialize the agent registry with all available agents"""
        self._agents = {}
        self._initialized = False
        
    def initialize(self) -> bool:
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
                "message_analysis": "available" if self._agents.get('message_analysis') else "not_available"
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
            return message_agent.analyze_patient_message(
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
            return message_agent.doctor_decision(followup_id, decision, custom_message)
        except Exception as e:
            logger.error(f"Error processing doctor's decision: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance - will be initialized when the server starts
agent_registry = AgentRegistry()
