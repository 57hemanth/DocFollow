from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from bson import ObjectId
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        return core_schema.json_schema(
            type='string',
            examples=['5eb7cf3a86d9755df3a6c593'],
        )

class DoctorBase(BaseModel):
    name: str
    email: EmailStr

class DoctorCreate(DoctorBase):
    password: str

class Doctor(DoctorBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    whatsapp_connected: bool = False
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: bool = False
    settings: Optional[dict] = None

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
