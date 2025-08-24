from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Remainder(BaseModel):
    doctor_id: str
    patient_id: str
    followup_date: datetime
    message_template: Optional[str] = None
    status: str = "pending"  # pending, sent, completed, failed
    created_at: datetime = datetime.now()
    scheduled_job_id: Optional[str] = None  # APScheduler job ID
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None

class RemainderCreate(BaseModel):
    patient_id: str
    followup_date: datetime
    message_template: Optional[str] = None

class RemainderUpdate(BaseModel):
    followup_date: Optional[datetime] = None
    message_template: Optional[str] = None
    status: Optional[str] = None
