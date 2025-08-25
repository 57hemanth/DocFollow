from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime
from .patients import PyObjectId, Patient

class Message(BaseModel):
    sender: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class AppointmentDetails(BaseModel):
    event_title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    gcal_event_id: Optional[str] = None

class FollowupBase(BaseModel):
    patient_id: str
    doctor_id: str
    status: str = "waiting_for_patient"
    history: List[Message] = []
    raw_data: List[str] = []
    extracted_data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    gcal_auth_url: Optional[str] = None
    appointment_details: Optional[AppointmentDetails] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class FollowupCreate(BaseModel):
    patient_id: str
    doctor_id: str
    raw_data: List[str] = []
    followup_date: Optional[datetime] = None

class FollowupUpdate(BaseModel):
    status: Optional[str] = None
    history: Optional[List[Message]] = None
    raw_data: Optional[List[str]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    gcal_auth_url: Optional[str] = None
    appointment_details: Optional[AppointmentDetails] = None
    updated_at: datetime = Field(default_factory=datetime.now)

class Followup(FollowupBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    patient: Optional[Patient] = None

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
