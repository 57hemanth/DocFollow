from pydantic import BaseModel
from datetime import datetime

class Remainder(BaseModel):
    doctor_id: str
    patient_id: str
    followup_date: datetime
    message_template: str
    status: str = "pending"
