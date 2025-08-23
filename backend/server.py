from fastapi import FastAPI
from backend.routes import doctors, patients, followups, appointments, settings, webhooks, uploads
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Middleware
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(followups.router)
app.include_router(appointments.router)
app.include_router(settings.router)
app.include_router(webhooks.router)
app.include_router(uploads.router)

@app.get("/health")
def health_check():
    return { "status": "Super duper healthy!"}