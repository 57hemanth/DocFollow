from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime
from .patients import PyObjectId

class AppointmentBase(BaseModel):
    doctor_id: str
    patient_id: str
    datetime: datetime
    status: str = "scheduled"

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    datetime: Optional[datetime] = None
    status: Optional[str] = None

class Appointment(AppointmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
