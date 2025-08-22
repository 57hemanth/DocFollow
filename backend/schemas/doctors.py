from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from .patients import PyObjectId

class DoctorBase(BaseModel):
    name: str
    email: str
    whatsapp_connected: bool = False
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: bool = False
    settings: Optional[dict] = None

class DoctorCreate(DoctorBase):
    password: str

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    whatsapp_connected: Optional[bool] = None
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: Optional[bool] = None
    settings: Optional[dict] = None

class Doctor(DoctorBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class DoctorInDB(Doctor):
    hashed_password: str
