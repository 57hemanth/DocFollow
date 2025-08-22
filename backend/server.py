from fastapi import FastAPI
from backend.routes import patients, remainders, followups, appointments, settings, webhooks

app = FastAPI()

app.include_router(patients.router)
app.include_router(remainders.router)
app.include_router(followups.router)
app.include_router(appointments.router)
app.include_router(settings.router)
app.include_router(webhooks.router)

@app.get("/health")
def health_check():
    return { "status": "Super duper healthy!"}