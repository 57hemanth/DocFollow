from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from backend.schemas.remainders import Remainder, RemainderCreate, RemainderUpdate
from backend.database import db
from bson import ObjectId

router = APIRouter()

@router.post("/remainders", response_model=Remainder, status_code=status.HTTP_201_CREATED)
def create_remainder(remainder: RemainderCreate):
    remainder_dict = remainder.dict()
    result = db.remainders.insert_one(remainder_dict)
    created_remainder = db.remainders.find_one({"_id": result.inserted_id})
    return created_remainder

@router.get("/remainders", response_model=List[Remainder])
def get_remainders():
    remainders = list(db.remainders.find())
    return remainders

@router.get("/remainders/{remainder_id}", response_model=Remainder)
def get_remainder(remainder_id: str):
    if not ObjectId.is_valid(remainder_id):
        raise HTTPException(status_code=400, detail="Invalid remainder_id")
    remainder = db.remainders.find_one({"_id": ObjectId(remainder_id)})
    if remainder:
        return remainder
    raise HTTPException(status_code=404, detail="Remainder not found")

@router.put("/remainders/{remainder_id}", response_model=Remainder)
def update_remainder(remainder_id: str, remainder: RemainderUpdate = Body(...)):
    if not ObjectId.is_valid(remainder_id):
        raise HTTPException(status_code=400, detail="Invalid remainder_id")
    
    remainder_data = {k: v for k, v in remainder.dict().items() if v is not None}

    if len(remainder_data) >= 1:
        update_result = db.remainders.update_one(
            {"_id": ObjectId(remainder_id)}, {"$set": remainder_data}
        )

        if update_result.modified_count == 1:
            if (
                updated_remainder := db.remainders.find_one({"_id": ObjectId(remainder_id)})
            ) is not None:
                return updated_remainder

    if (
        existing_remainder := db.remainders.find_one({"_id": ObjectId(remainder_id)})
    ) is not None:
        return existing_remainder

    raise HTTPException(status_code=404, detail=f"Remainder {remainder_id} not found")

@router.delete("/remainders/{remainder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_remainder(remainder_id: str):
    if not ObjectId.is_valid(remainder_id):
        raise HTTPException(status_code=400, detail="Invalid remainder_id")
    
    delete_result = db.remainders.delete_one({"_id": ObjectId(remainder_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Remainder not found")
