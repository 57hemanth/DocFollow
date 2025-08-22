from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.appointments import Appointment, AppointmentCreate, AppointmentUpdate
from backend.database import db
from bson import ObjectId

router = APIRouter()

@router.post("/appointments", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate):
    appointment_dict = appointment.dict()
    result = db.appointments.insert_one(appointment_dict)
    created_appointment = db.appointments.find_one({"_id": result.inserted_id})
    return created_appointment

@router.get("/appointments", response_model=List[Appointment])
def get_appointments():
    appointments = list(db.appointments.find())
    return appointments

@router.get("/appointments/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: str):
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment_id")
    appointment = db.appointments.find_one({"_id": ObjectId(appointment_id)})
    if appointment:
        return appointment
    raise HTTPException(status_code=404, detail="Appointment not found")

@router.put("/appointments/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: str, appointment: AppointmentUpdate = Body(...)):
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment_id")
    
    appointment_data = {k: v for k, v in appointment.dict().items() if v is not None}

    if len(appointment_data) >= 1:
        update_result = db.appointments.update_one(
            {"_id": ObjectId(appointment_id)}, {"$set": appointment_data}
        )

        if update_result.modified_count == 1:
            if (
                updated_appointment := db.appointments.find_one({"_id": ObjectId(appointment_id)})
            ) is not None:
                return updated_appointment

    if (
        existing_appointment := db.appointments.find_one({"_id": ObjectId(appointment_id)})
    ) is not None:
        return existing_appointment

    raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")

@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: str):
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment_id")
    
    delete_result = db.appointments.delete_one({"_id": ObjectId(appointment_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
