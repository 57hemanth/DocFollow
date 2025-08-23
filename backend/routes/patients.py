from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.patients import Patient, PatientCreate, PatientUpdate
from backend.database import db
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate):
    patient_dict = patient.dict(exclude={"followup_date", "followup_time"})
    result = db.patients.insert_one(patient_dict)
    created_patient = db.patients.find_one({"_id": result.inserted_id})

    # Create followup record if followup date and time are provided
    if patient.followup_date and patient.followup_time:
        try:
            # Parse date and time strings
            followup_date = datetime.strptime(patient.followup_date, '%Y-%m-%d').date()
            followup_time = datetime.strptime(patient.followup_time, '%H:%M').time()
            followup_datetime = datetime.combine(followup_date, followup_time)
            
            followup_data = {
                "doctor_id": patient.doctor_id,
                "patient_id": str(result.inserted_id),
                "original_data": [f"Scheduled follow-up for {patient.name}"],
                "extracted_data": {"scheduled_datetime": followup_datetime.isoformat()},
                "ai_draft_message": f"Follow-up scheduled for {patient.name} on {followup_datetime.strftime('%Y-%m-%d at %H:%M')}",
                "doctor_decision": "scheduled",
                "final_message_sent": False,
                "created_at": followup_datetime
            }
            db.followups.insert_one(followup_data)
            created_patient["followup_date"] = followup_datetime.isoformat()
        except ValueError as e:
            # If date/time parsing fails, continue without creating followup
            print(f"Error parsing followup date/time: {e}")
            created_patient["followup_date"] = None
    else:
        # Check if any existing followup exists
        followup = db.followups.find_one({"patient_id": str(result.inserted_id)})
        if followup:
            created_patient["followup_date"] = followup["created_at"].isoformat()
        else:
            created_patient["followup_date"] = None

    return created_patient

@router.get("/patients", response_model=List[Patient])
def get_patients():
    patients = list(db.patients.find())
    
    # Enrich patients with followup date from followups
    for patient in patients:
        patient_id = str(patient["_id"])
        followup = db.followups.find_one({"patient_id": patient_id})
        if followup:
            patient["followup_date"] = followup["created_at"].isoformat()
        else:
            patient["followup_date"] = None
    
    return patients

@router.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    patient = db.patients.find_one({"_id": ObjectId(patient_id)})
    if patient:
        # Enrich patient with followup date from followups
        followup = db.followups.find_one({"patient_id": patient_id})
        if followup:
            patient["followup_date"] = followup["created_at"].isoformat()
        else:
            patient["followup_date"] = None
        return patient
    raise HTTPException(status_code=404, detail="Patient not found")

@router.put("/patients/{patient_id}", response_model=Patient)
def update_patient(patient_id: str, patient: PatientUpdate = Body(...)):
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    
    patient_data = {k: v for k, v in patient.dict().items() if v is not None}

    if len(patient_data) >= 1:
        update_result = db.patients.update_one(
            {"_id": ObjectId(patient_id)}, {"$set": patient_data}
        )

        if update_result.modified_count == 1:
            if (
                updated_patient := db.patients.find_one({"_id": ObjectId(patient_id)})
            ) is not None:
                return updated_patient

    if (
        existing_patient := db.patients.find_one({"_id": ObjectId(patient_id)})
    ) is not None:
        return existing_patient

    raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str):
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    
    delete_result = db.patients.delete_one({"_id": ObjectId(patient_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
