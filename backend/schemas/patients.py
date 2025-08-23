from pydantic import BaseModel, Field
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


class PatientBase(BaseModel):
    doctor_id: str
    name: str
    disease: str
    phone: str
    address: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None

class PatientCreate(PatientBase):
    followup_date: Optional[str] = None
    followup_time: Optional[str] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    disease: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None

class Patient(PatientBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    followup_date: Optional[str] = None

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
