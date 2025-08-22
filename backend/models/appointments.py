from pydantic import BaseModel
from datetime import datetime

class Appointment(BaseModel):
    doctor_id: str
    patient_id: str
    datetime: datetime
    status: str = "scheduled"
