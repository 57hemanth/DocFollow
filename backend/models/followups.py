from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Followup(BaseModel):
    patient_id: str
    doctor_id: str
    original_data: List[str]
    extracted_data: Optional[dict] = None
    ai_draft_message: Optional[str] = None
    doctor_decision: Optional[str] = None
    final_message_sent: bool = False
    created_at: datetime = datetime.now()
