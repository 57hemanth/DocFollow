"""
Appointment Agent for DocFollow - Manages appointment scheduling and booking.
"""

from portia import Portia, Config, PlanBuilder, McpToolRegistry, DefaultToolRegistry, Clarification
from backend.config import PORTIA_LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
from backend.database import db
from backend.models.patients import Patient
from backend.services.whatsapp_service import whatsapp_service
import logging
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
import asyncio
from portia import StepOutput

logger = logging.getLogger(__name__)

class AppointmentAgent:
    """
    AI agent responsible for managing appointment scheduling workflows including:
    - Sending messages to patients to ask for their availability
    - Creating appointments using Google Calendar
    - Handling authentication with Google Calendar
    """
    
    def __init__(self, portia_instance: Portia):
        """
        Initialize the Appointment Agent with a Portia instance.
        """
        self.portia = portia_instance
        self.db = db
    
    async def start_appointment_booking(self, followup_id: str, patient_id: str, doctor_id: str):
        """
        Starts the appointment booking process by sending a message to the patient.
        """
        try:
            patient = self.db.patients.find_one({"_id": ObjectId(patient_id)})
            if not patient:
                logger.error(f"Patient with ID {patient_id} not found.")
                return

            message = "Doctor is suggest to take appointment. Please let me know when you are free I will create an appoitment for you. Please let me know date and time"
            
            # Send the message directly using the whatsapp_service
            result = await whatsapp_service.send_message(patient['phone'], message)

            if not result.get("success"):
                logger.error(f"Failed to send WhatsApp message for followup {followup_id}: {result.get('error')}")
                return

            # Log the message and update the followup status
            new_message_log = {
                "sender": "agent",
                "content": message,
                "timestamp": datetime.now()
            }
            self.db.followups.update_one(
                {"_id": ObjectId(followup_id)},
                {
                    "$push": {"history": new_message_log},
                    "$set": {
                        "status": "appointment_scheduling",
                        "updated_at": datetime.now()
                    }
                }
            )
            
            logger.info(f"Sent appointment scheduling request to patient {patient_id} for followup {followup_id}")

        except Exception as e:
            logger.error(f"Error starting appointment booking for followup {followup_id}: {e}")

    async def book_appointment(self, followup_id: str, patient_id: str, doctor_id: str, patient_response: str):
        """
        Books an appointment based on the patient's response.
        """
        try:
            logger.info(f"--- Starting appointment booking for followup_id: {followup_id} ---")
            logger.info(f"Patient ID: {patient_id}, Doctor ID: {doctor_id}")
            logger.info(f"Patient Response: '{patient_response}'")

            patient = self.db.patients.find_one({"_id": ObjectId(patient_id)})
            doctor = self.db.doctors.find_one({"_id": ObjectId(doctor_id)})

            logger.info(f"Patient object from DB: {patient}")
            logger.info(f"Doctor object from DB: {doctor}")

            if not patient or not doctor:
                logger.error(f"Patient or doctor not found for followup {followup_id}")
                return

            patient_email = patient.get('email')
            doctor_email = doctor.get('email')

            if not doctor_email:
                logger.error(f"Doctor email missing for followup {followup_id}")
                return

            instruction = f"""
            The patient {patient.get('name', 'N/A')} has requested to book an appointment and provided their availability: '{patient_response}'.
            Your task is to create a Google Calendar event for the appointment.
            The event title should be "Appointment with {patient.get('name', 'N/A')}".
            The attendees should be the doctor '{doctor_email}'.
            The event description should be "Follow-up appointment for {patient.get('name', 'N/A')}".
            If you need to ask for clarification, do so.
            """
            logger.info(f"Instruction sent to Portia: {instruction}")

            plan_run = await asyncio.to_thread(self.portia.run, instruction)

            logger.info(f"Portia plan run completed. Result: {plan_run}")

            if plan_run.state == "NEED_CLARIFICATION" and plan_run.outputs.clarifications:
                clarification = plan_run.outputs.clarifications[0]
                if clarification.category == "ACTION":
                    auth_url = clarification.action_url
                    self.db.followups.update_one(
                        {"_id": ObjectId(followup_id)},
                        {"$set": {"gcal_auth_url": auth_url}}
                    )
                    logger.info(f"Google Calendar authentication required for followup {followup_id}. Auth URL: {auth_url}")
                    
                    # Wait for the doctor to authenticate and get the updated plan_run
                    plan_run = await self.portia.wait_for_ready(plan_run.id)
                    logger.info(f"Authentication complete. Refreshed plan_run: {plan_run!r}")

            # If the plan was successful, extract event details and update the followup
            if plan_run.outputs and plan_run.outputs.step_outputs:
                # Get the output from the last step
                last_step_index = max(plan_run.outputs.step_outputs.keys())
                last_step = plan_run.outputs.step_outputs[last_step_index]

                if isinstance(last_step, StepOutput) and last_step.tool_id == "portia:google:gcalendar:create_event":
                    event_details = last_step.output
                    
                    appointment_data = {
                        "event_title": event_details.get("summary"),
                        "start_time": event_details.get("start", {}).get("dateTime"),
                        "end_time": event_details.get("end", {}).get("dateTime"),
                        "gcal_event_id": event_details.get("id"),
                    }
                    
                    update_result = self.db.followups.update_one(
                        {"_id": ObjectId(followup_id)},
                        {
                            "$set": {
                                "status": "completed",
                                "appointment_details": appointment_data,
                                "updated_at": datetime.now()
                            }
                        }
                    )
                    
                    if update_result.modified_count == 0:
                        logger.error(f"Failed to update followup document for followup_id: {followup_id}")
                    else:
                        logger.info(f"Successfully updated followup document for followup_id: {followup_id}")
            
                    confirmation_message = (
                        f"Your appointment with Dr. {doctor.get('name', 'N/A')} has been confirmed.\n"
                        f"Title: {appointment_data['event_title']}\n"
                        f"Time: {appointment_data['start_time']}"
                    )
                    await whatsapp_service.send_message(patient['phone'], confirmation_message)
                    logger.info(f"Successfully booked appointment for followup {followup_id}")

            logger.info(f"Appointment booking process initiated for followup {followup_id}. Plan run state: {plan_run!r}")
            logger.info(f"--- Finished appointment booking for followup_id: {followup_id} ---")
        
        except Exception as e:
            logger.error(f"Error booking appointment for followup {followup_id}: {e}", exc_info=True)
