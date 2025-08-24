import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        )

    def upload_file(self, file_path, resource_type="auto"):
        try:
            upload_result = cloudinary.uploader.upload(
                file_path, resource_type=resource_type
            )
            return upload_result
        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")
            return None

cloudinary_service = CloudinaryService()
