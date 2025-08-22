from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.patients import Patient, PatientCreate, PatientUpdate
from backend.database import db
from bson import ObjectId

router = APIRouter()

@router.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate):
    patient_dict = patient.dict()
    result = db.patients.insert_one(patient_dict)
    created_patient = db.patients.find_one({"_id": result.inserted_id})
    return created_patient

@router.get("/patients", response_model=List[Patient])
def get_patients():
    patients = list(db.patients.find())
    return patients

@router.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    patient = db.patients.find_one({"_id": ObjectId(patient_id)})
    if patient:
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
