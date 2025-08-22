from pydantic import BaseModel
from typing import Optional

class Doctor(BaseModel):
    name: str
    email: str
    password_hash: str
    whatsapp_connected: bool = False
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: bool = False
    settings: Optional[dict] = None
