from fastapi import FastAPI
from backend.routes import doctors, patients, followups, appointments, settings, webhooks, uploads
from backend.routes import agents
from backend.agents import agent_registry
from backend.services.scheduler_service import scheduler_service
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DocFollow API", description="AI-powered patient follow-up assistant")

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
app.include_router(agents.router)

@app.on_event("startup")
async def startup_event():
    """Initialize AI agents and scheduler on server startup"""
    logger.info("🚀 Starting DocFollow server...")
    
    try:
        # Initialize scheduler service first
        scheduler_success = await scheduler_service.initialize()
        if scheduler_success:
            logger.info("✅ Scheduler service initialized successfully")
        else:
            logger.warning("⚠️ Scheduler service failed to initialize")
        
        # Initialize AI agents
        agent_success = await agent_registry.initialize()
        if agent_success:
            logger.info("✅ AI agents initialized successfully")
        else:
            logger.warning("⚠️ Some AI agents failed to initialize")
            
        if scheduler_success and agent_success:
            logger.info("🎉 DocFollow server started successfully with all services")
        else:
            logger.warning("⚠️ DocFollow server started with some service failures")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown services"""
    logger.info("🛑 Shutting down DocFollow server...")
    
    try:
        # Shutdown scheduler service
        await scheduler_service.shutdown()
        logger.info("✅ Scheduler service shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

@app.get("/health")
def health_check():
    return {
        "status": "Super duper healthy!",
        "agents": agent_registry.get_agent_status(),
        "scheduler": {
            "initialized": scheduler_service.is_initialized(),
            "jobs": scheduler_service.get_scheduled_jobs() if scheduler_service.is_initialized() else {}
        }
    }