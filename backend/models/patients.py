from pydantic import BaseModel
from typing import Optional

class Patient(BaseModel):
    doctor_id: str
    name: str
    diagnosis: str
    phone: str
    address: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
