from fastapi import APIRouter, Body, HTTPException, status
from backend.schemas.settings import Settings
from backend.database import db
from bson import ObjectId

router = APIRouter()

@router.get("/settings/{doctor_id}", response_model=Settings)
def get_settings(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")
    
    doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    
    if doctor:
        # We construct the settings from the doctor document
        # Pydantic will validate and use defaults for missing fields
        return Settings(**doctor)
        
    raise HTTPException(status_code=404, detail="Doctor not found")

@router.put("/settings/{doctor_id}", response_model=Settings)
def update_settings(doctor_id: str, settings: Settings = Body(...)):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    settings_data = {k: v for k, v in settings.dict().items() if v is not None}

    update_result = db.doctors.update_one(
        {"_id": ObjectId(doctor_id)}, {"$set": settings_data}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found")

    if (
        updated_doctor := db.doctors.find_one({"_id": ObjectId(doctor_id)})
    ) is not None:
        return Settings(**updated_doctor)

    raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found after update")
