from fastapi import APIRouter, Body, HTTPException, status
from typing import List, Dict, Any
from backend.schemas.followups import Followup, FollowupCreate, FollowupUpdate
from backend.database import db
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/followups", response_model=Followup, status_code=status.HTTP_201_CREATED)
def create_followup(followup: FollowupCreate):
    followup_dict = followup.dict()
    result = db.followups.insert_one(followup_dict)
    created_followup = db.followups.find_one({"_id": result.inserted_id})
    return created_followup

@router.get("/followups", response_model=List[Followup])
def get_followups():
    followups = list(db.followups.find())
    return followups

@router.get("/followups/with-patients", response_model=List[Dict[str, Any]])
def get_followups_with_patients():
    """
    Get all follow-ups with enriched patient data from remainders and patients collections
    """
    try:
        # Get remainders and manually join with patients for more reliable data
        remainders = list(db.remainders.find())
        
        enriched_followups = []
        for remainder in remainders:
            # Get patient information - handle ObjectId conversion
            patient_id = remainder["patient_id"]
            if isinstance(patient_id, str) and ObjectId.is_valid(patient_id):
                patient_id = ObjectId(patient_id)
            patient = db.patients.find_one({"_id": patient_id})
            
            # Get followup records for this patient  
            followup_records = list(db.followups.find({"patient_id": remainder["patient_id"]}))
            
            # Build the enriched follow-up record
            enriched_followup = {
                "_id": str(remainder["_id"]),
                "patient_id": str(remainder["patient_id"]),
                "patient_name": patient["name"] if patient else "Unknown Patient",
                "patient_phone": patient["phone"] if patient else "N/A", 
                "patient_diagnosis": patient["diagnosis"] if patient else "N/A",  # Fixed: use 'diagnosis' not 'disease'
                "followup_date": remainder["followup_date"].isoformat() if hasattr(remainder["followup_date"], 'isoformat') else str(remainder["followup_date"]),
                "message_template": remainder.get("message_template", ""),
                "status": remainder.get("status", "pending"),
                "created_at": remainder["created_at"].isoformat() if hasattr(remainder["created_at"], 'isoformat') else str(remainder["created_at"]),
                "scheduled_job_id": remainder.get("scheduled_job_id"),
                "attempts": remainder.get("attempts", 0),
                "last_attempt": remainder["last_attempt"].isoformat() if remainder.get("last_attempt") and hasattr(remainder["last_attempt"], 'isoformat') else None,
                "error_message": remainder.get("error_message"),
                "message_sent": remainder.get("status") == "sent",
                "response_received": len(followup_records) > 0,
                "final_message_sent": remainder.get("status") == "completed"
            }
            
            enriched_followups.append(enriched_followup)
        
        # Sort by followup_date
        enriched_followups.sort(key=lambda x: x["followup_date"])
        
        logger.info(f"Retrieved {len(enriched_followups)} follow-ups with patient data")
        return enriched_followups
        
    except Exception as e:
        logger.error(f"Error fetching follow-ups with patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch follow-ups: {str(e)}")

@router.get("/followups/{followup_id}", response_model=Followup)
def get_followup(followup_id: str):
    if not ObjectId.is_valid(followup_id):
        raise HTTPException(status_code=400, detail="Invalid followup_id")
    followup = db.followups.find_one({"_id": ObjectId(followup_id)})
    if followup:
        return followup
    raise HTTPException(status_code=404, detail="Followup not found")

@router.put("/followups/{followup_id}", response_model=Followup)
def update_followup(followup_id: str, followup: FollowupUpdate = Body(...)):
    if not ObjectId.is_valid(followup_id):
        raise HTTPException(status_code=400, detail="Invalid followup_id")
    
    followup_data = {k: v for k, v in followup.dict().items() if v is not None}

    if len(followup_data) >= 1:
        update_result = db.followups.update_one(
            {"_id": ObjectId(followup_id)}, {"$set": followup_data}
        )

        if update_result.modified_count == 1:
            if (
                updated_followup := db.followups.find_one({"_id": ObjectId(followup_id)})
            ) is not None:
                return updated_followup

    if (
        existing_followup := db.followups.find_one({"_id": ObjectId(followup_id)})
    ) is not None:
        return existing_followup

    raise HTTPException(status_code=404, detail=f"Followup {followup_id} not found")

@router.delete("/followups/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_followup(followup_id: str):
    if not ObjectId.is_valid(followup_id):
        raise HTTPException(status_code=400, detail="Invalid followup_id")
    
    delete_result = db.followups.delete_one({"_id": ObjectId(followup_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Followup not found")
