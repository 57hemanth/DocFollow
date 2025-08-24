from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime
from .patients import PyObjectId

class Message(BaseModel):
    sender: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class FollowupBase(BaseModel):
    patient_id: str
    doctor_id: str
    status: str = "waiting_for_patient"
    history: List[Message] = []
    original_data: List[str] = []
    extracted_data: Optional[Dict[str, Any]] = None
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

class Followup(FollowupBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
