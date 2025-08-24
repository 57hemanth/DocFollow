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
    status: str = "waiting_for_patient"  # waiting_for_patient, waiting_for_doctor, closed
    history: List[Message] = []
    original_data: List[str] = []
    extracted_data: Optional[dict] = None
    note: Optional[str] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class FollowupCreate(BaseModel):
    patient_id: str
    doctor_id: str

class FollowupUpdate(BaseModel):
    status: Optional[str] = None
    history: Optional[List[Message]] = None
    original_data: Optional[List[str]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)
