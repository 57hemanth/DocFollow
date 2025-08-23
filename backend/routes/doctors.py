from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from backend.database import db
from backend.schemas.doctors import Doctor, DoctorCreate
from bson import ObjectId

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/doctors/signup", response_model=Doctor, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: DoctorCreate):
    # Check if doctor already exists
    if db.doctors.find_one({"email": doctor.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = pwd_context.hash(doctor.password)
    
    # Create the doctor document
    doctor_data = doctor.dict(exclude={"password"})
    doctor_data["password_hash"] = hashed_password

    # Insert the new doctor into the database
    result = db.doctors.insert_one(doctor_data)
    new_doctor = db.doctors.find_one({"_id": result.inserted_id})
    
    return new_doctor
