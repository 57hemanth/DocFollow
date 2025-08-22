from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    whatsapp_connected: bool = False
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: bool = False
    notifications: Optional[dict] = None
