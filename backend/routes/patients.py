from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.patients import Patient, PatientCreate, PatientUpdate
from backend.database import db
from backend.services.scheduler_service import scheduler_service
from bson import ObjectId
from datetime import datetime, time
import logging
from backend.schemas.doctors import Doctor  # Import the Doctor schema

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate):
    # Validate the doctor_id
    if not ObjectId.is_valid(patient.doctor_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doctor_id: '{patient.doctor_id}'. Must be a 24-character hex string."
        )
    
    doctor_object_id = ObjectId(patient.doctor_id)

    # Check if the doctor exists
    doctor = db.doctors.find_one({"_id": doctor_object_id})
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {patient.doctor_id} not found")

    patient_dict = patient.dict(exclude={"followup_date", "followup_time"})
    patient_dict["doctor_id"] = doctor_object_id  # Ensure it's the ObjectId
    result = db.patients.insert_one(patient_dict)
    created_patient = db.patients.find_one({"_id": result.inserted_id})
    patient_id = str(result.inserted_id)

    # Create followup record and schedule reminder if followup date and time are provided
    if patient.followup_date and patient.followup_time:
        try:
            # Parse date and time strings
            followup_date = datetime.strptime(patient.followup_date, '%Y-%m-%d').date()
            followup_time = datetime.strptime(patient.followup_time, '%H:%M').time()
            followup_datetime = datetime.combine(followup_date, followup_time)
            
            # Create followup record
            followup_data = {
                "doctor_id": doctor_object_id,
                "patient_id": patient_id,
                "original_data": [f"Scheduled follow-up for {patient.name}"],
                "extracted_data": {"scheduled_datetime": followup_datetime.isoformat()},
                "ai_draft_message": f"Follow-up scheduled for {patient.name} on {followup_datetime.strftime('%Y-%m-%d at %H:%M')}",
                "doctor_decision": "scheduled",
                "final_message_sent": False,
                "created_at": followup_datetime
            }
            db.followups.insert_one(followup_data)
            
            # Create remainder record for scheduling
            remainder_data = {
                "doctor_id": doctor_object_id,
                "patient_id": patient_id,
                "followup_date": followup_datetime,
                "message_template": f"Follow-up reminder for {patient.name}",
                "status": "pending",
                "created_at": datetime.now(),
                "scheduled_job_id": None,
                "attempts": 0,
                "last_attempt": None,
                "error_message": None
            }
            remainder_result = db.remainders.insert_one(remainder_data)
            remainder_id = str(remainder_result.inserted_id)
            
            # Schedule the follow-up reminder (24 hours before appointment)
            if scheduler_service.is_initialized():
                job_id = await scheduler_service.schedule_follow_up_reminder(
                    remainder_id=remainder_id,
                    patient_id=patient_id,
                    doctor_id=patient.doctor_id,
                    followup_datetime=followup_datetime,
                    advance_hours=24  # Send reminder 24 hours before
                )
                
                if job_id:
                    logger.info(f"✅ Follow-up reminder scheduled for patient {patient.name} (Job: {job_id})")
                    created_patient["scheduled_reminder"] = True
                    created_patient["reminder_job_id"] = job_id
                else:
                    logger.warning(f"⚠️ Failed to schedule reminder for patient {patient.name}")
                    created_patient["scheduled_reminder"] = False
            else:
                logger.warning("⚠️ Scheduler service not initialized")
                created_patient["scheduled_reminder"] = False
            
            created_patient["followup_date"] = followup_datetime.isoformat()
            created_patient["remainder_id"] = remainder_id
            
        except ValueError as e:
            # If date/time parsing fails, continue without creating followup
            logger.error(f"Error parsing followup date/time: {e}")
            created_patient["followup_date"] = None
            created_patient["scheduled_reminder"] = False
    else:
        # Check if any existing followup exists
        followup = db.followups.find_one({"patient_id": patient_id})
        if followup:
            created_patient["followup_date"] = followup["created_at"].isoformat()
        else:
            created_patient["followup_date"] = None
        created_patient["scheduled_reminder"] = False

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


@router.post("/patients/{patient_id}/reschedule", status_code=status.HTTP_200_OK)
async def reschedule_followup(patient_id: str, new_date: str = Body(...), new_time: str = Body(...)):
    """Reschedule all reminders for a patient for a new date and time."""
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient_id")

    try:
        new_followup_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        new_followup_time = datetime.strptime(new_time, '%H:%M').time()
        new_followup_datetime = datetime.combine(new_followup_date, new_followup_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYY-MM-DD and HH:MM.")

    if new_followup_datetime <= datetime.now():
        raise HTTPException(status_code=400, detail="Follow-up date must be in the future.")

    # Find all reminders for the patient
    reminders = list(db.remainders.find({"patient_id": patient_id}))

    if not reminders:
        raise HTTPException(status_code=404, detail="No reminders found for this patient.")

    updated_count = 0
    for reminder in reminders:
        try:
            # Cancel the old job
            if reminder.get("scheduled_job_id") and scheduler_service.is_initialized():
                await scheduler_service.cancel_follow_up_reminder(reminder["scheduled_job_id"])

            # Schedule a new job
            if scheduler_service.is_initialized():
                new_job_id = await scheduler_service.schedule_follow_up_reminder(
                    remainder_id=str(reminder["_id"]),
                    patient_id=patient_id,
                    doctor_id=reminder["doctor_id"],
                    followup_datetime=new_followup_datetime,
                    advance_hours=24
                )
            else:
                new_job_id = None

            # Update the reminder
            db.remainders.update_one(
                {"_id": reminder["_id"]},
                {"$set": {
                    "followup_date": new_followup_datetime,
                    "scheduled_job_id": new_job_id,
                    "status": "pending" if new_job_id else "failed"
                }}
            )

            # Also update the corresponding followup created_at time
            db.followups.update_many(
                {"patient_id": patient_id},
                {"$set": {"created_at": new_followup_datetime}}
            )
            
            updated_count += 1

        except Exception as e:
            logger.error(f"Error rescheduling reminder {reminder['_id']}: {e}")
            # Optionally, you can decide how to handle partial failures
            continue

    return {"message": f"Successfully rescheduled {updated_count} reminder(s)."}
