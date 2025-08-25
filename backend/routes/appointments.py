from fastapi import APIRouter, Body, HTTPException, status, Query
from typing import List
from backend.schemas.appointments import Appointment
from backend.database import db
from bson import ObjectId

router = APIRouter()

# Note: The AppointmentCreate and AppointmentUpdate schemas are intentionally omitted
# as they are not used in the updated code.

@router.get("/appointments", response_model=List[Appointment])
def get_appointments(doctor_id: str = Query(None)):
    query = {}
    if doctor_id:
        query["doctor_id"] = doctor_id
    
    appointments_cursor = db.appointments.find(query)
    appointments = []
    for appointment in appointments_cursor:
        patient = db.patients.find_one({"_id": ObjectId(appointment["patient_id"])})
        appointment["patient"] = patient
        appointments.append(appointment)
        
    return appointments

@router.get("/appointments/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: str):
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment_id")
    
    appointment = db.appointments.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    patient = db.patients.find_one({"_id": ObjectId(appointment["patient_id"])})
    appointment["patient"] = patient
    
    return appointment
