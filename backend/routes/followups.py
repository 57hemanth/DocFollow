from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.followups import Followup, FollowupCreate, FollowupUpdate
from backend.database import db
from bson import ObjectId

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
