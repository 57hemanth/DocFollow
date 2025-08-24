from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    sender: str  # "agent" or "patient"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Followup(BaseModel):
    patient_id: str
    doctor_id: str
    followup_date: datetime
    message_template: Optional[str] = None
    status: str = "pending"  # pending, sent, completed, failed
    history: List[Message] = []
    original_data: Optional[List[str]] = None
    extracted_data: Optional[dict] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    final_message_sent: bool = False
    created_at: datetime = datetime.now()
    scheduled_job_id: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None

class FollowupCreate(BaseModel):
    patient_id: str
    followup_date: datetime
    message_template: Optional[str] = None

class FollowupUpdate(BaseModel):
    followup_date: Optional[datetime] = None
    message_template: Optional[str] = None
    status: Optional[str] = None
    original_data: Optional[List[str]] = None
    extracted_data: Optional[dict] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    final_message_sent: Optional[bool] = None
    history: Optional[List[Message]] = None
