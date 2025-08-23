from fastapi import APIRouter, File, UploadFile
from cloudinary.uploader import upload
from backend.config import cloudinary

router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        result = upload(file.file)
        return {"url": result["secure_url"]}
    except Exception as e:
        return {"error": str(e)}
