from pydantic import BaseModel, EmailStr
from typing import Optional

class Settings(BaseModel):
    name: str
    email: EmailStr
    whatsapp_connected: bool = False
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: bool = False
    notifications: Optional[dict] = None

class SettingsUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp_connected: Optional[bool] = None
    whatsapp_number: Optional[str] = None
    whatsapp_sandbox_id: Optional[str] = None
    google_calendar_connected: Optional[bool] = None
    notifications: Optional[dict] = None
