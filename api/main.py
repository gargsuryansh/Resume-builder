from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Explicit Route Imports
from api.routes.resume import router as resume_router
from api.routes.candidate import router as candidate_router
from api.routes.auth import router as auth_router
from api.routes.jobs import router as jobs_router
from api.routes.builder import router as builder_router
from api.routes.dashboard import router as dashboard_router
from api.routes.feedback import router as feedback_router

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and Shutdown logic.
    """
    logger.info("🚀 Smart AI Resume Analyzer Starting...")
    yield
    logger.info("💤 Smart AI Resume Analyzer Shutting Down...")

# App Initialization
app = FastAPI(
    title="Smart AI Resume Analyzer API",
    description="Enterprise-grade AI-powered resume parsing and candidate management.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # React Dev Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System Endpoints
@app.get("/", tags=["System"])
def read_root():
    return {
        "message": "Welcome to Smart AI Resume Analyzer API",
        "documentation": "/docs",
        "status": "Running"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}

# Include Modular Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(resume_router)
app.include_router(candidate_router)
app.include_router(jobs_router)
app.include_router(builder_router)
app.include_router(dashboard_router)
app.include_router(feedback_router)

# Note: Feedback system and OpenRouter-ready analyzer are now active.
