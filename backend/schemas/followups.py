from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from .patients import PyObjectId

class FollowupBase(BaseModel):
    patient_id: str
    doctor_id: str
    original_data: List[str]
    extracted_data: Optional[dict] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    final_message_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class FollowupCreate(FollowupBase):
    pass

class FollowupUpdate(BaseModel):
    extracted_data: Optional[dict] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    final_message_sent: Optional[bool] = None

class Followup(FollowupBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
