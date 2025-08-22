from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime
from .patients import PyObjectId

class RemainderBase(BaseModel):
    doctor_id: str
    patient_id: str
    followup_date: datetime
    message_template: str
    status: str = "pending"

class RemainderCreate(RemainderBase):
    pass

class RemainderUpdate(BaseModel):
    followup_date: Optional[datetime] = None
    message_template: Optional[str] = None
    status: Optional[str] = None

class Remainder(RemainderBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
