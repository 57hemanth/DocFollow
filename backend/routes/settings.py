from fastapi import APIRouter, Body, HTTPException, status
from backend.schemas.settings import Settings
from backend.schemas.doctors import Doctor, DoctorUpdate
from backend.database import db
from backend.services.whatsapp_service import whatsapp_service
from bson import ObjectId
from typing import Dict, Any
from datetime import datetime

router = APIRouter()

@router.get("/settings/{doctor_id}", response_model=Doctor)
def get_settings(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")
    
    doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    
    if doctor:
        return doctor
        
    raise HTTPException(status_code=404, detail="Doctor not found")

@router.put("/settings/{doctor_id}", response_model=Doctor)
def update_settings(doctor_id: str, settings: DoctorUpdate = Body(...)):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    settings_data = {k: v for k, v in settings.dict(exclude_unset=True).items()}

    if not settings_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    update_result = db.doctors.update_one(
        {"_id": ObjectId(doctor_id)}, {"$set": settings_data}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found")

    if (
        updated_doctor := db.doctors.find_one({"_id": ObjectId(doctor_id)})
    ) is not None:
        return updated_doctor

    raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found after update")

@router.get("/settings/whatsapp/sandbox-info")
async def get_whatsapp_sandbox_info():
    """Get WhatsApp Sandbox setup instructions"""
    return whatsapp_service.get_sandbox_instructions()

@router.post("/settings/{doctor_id}/whatsapp/test")
async def test_whatsapp_connection(doctor_id: str, test_data: Dict[str, str] = Body(...)):
    """Test WhatsApp connection by sending a test message"""
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")
    
    phone_number = test_data.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required")
    
    # Get doctor info
    doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    test_message = f"""
    Hello! This is from Dr. {doctor.get('name', 'Unknown')}. How are you?
    """.strip()
    
    result = await whatsapp_service.send_message(phone_number, test_message)
    
    if result["success"]:
        # Update doctor's WhatsApp connection status
        update_result = db.doctors.update_one(
            {"_id": ObjectId(doctor_id)},
            {"$set": {"whatsapp_connected": True, "whatsapp_number": phone_number}}
        )
        
        if update_result.matched_count > 0:
            updated_doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
            return {
                "status": "success", 
                "message": "Test message sent successfully", 
                "result": result,
                "updated_settings": Settings(**updated_doctor).dict()
            }
        else:
            # This case would be rare, as we check for the doctor earlier
            return {"status": "error", "message": "Failed to find doctor to update connection status"}
    else:
        return {"status": "error", "message": f"Failed to send test message: {result['error']}"}

@router.post("/settings/{doctor_id}/whatsapp/send-reminder")
async def send_follow_up_reminder(doctor_id: str, reminder_data: Dict[str, Any] = Body(...)):
    """Send a follow-up reminder to a patient"""
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")
    
    required_fields = ["patient_id", "follow_up_date"]
    for field in required_fields:
        if field not in reminder_data:
            raise HTTPException(status_code=400, detail=f"{field} is required")
    
    # Get doctor and patient info
    doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    patient = db.patients.find_one({"_id": ObjectId(reminder_data["patient_id"])})
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    result = await whatsapp_service.send_follow_up_reminder(
        patient_phone=patient.get("phone"),
        patient_name=patient.get("name"),
        doctor_name=doctor.get("name"),
        follow_up_date=reminder_data["follow_up_date"]
    )
    
    if result["success"]:
        # Create followup record to track the reminder
        followup_data = {
            "doctor_id": doctor_id,
            "patient_id": reminder_data["patient_id"],
            "original_data": ["follow_up_reminder"],
            "ai_draft_message": f"Follow-up reminder sent on {reminder_data['follow_up_date']}",
            "doctor_decision": "approved",
            "final_message_sent": True,
            "created_at": datetime.now()
        }
        
        db.followups.insert_one(followup_data)
        
        return {"status": "success", "message": "Follow-up reminder sent", "result": result}
    else:
        return {"status": "error", "message": f"Failed to send reminder: {result['error']}"}
