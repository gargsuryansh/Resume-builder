from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Explicit Route Imports to avoid any module resolution issues
from api.routes.resume import router as resume_router
from api.routes.candidate import router as candidate_router
from api.routes.auth import router as auth_router

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
    allow_origins=["http://localhost:5173"], 
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
# Note: Auth routes are mounted with prefix="/auth" as requested.
# Swagger UI will display them under the "Authentication" tag.
app.include_router(auth_router, prefix="/auth")
app.include_router(resume_router)
app.include_router(candidate_router)

# Note: Ensure that the 'auth_router' in api/routes/auth.py 
# does NOT have its own prefix to avoid double-prefixing.
