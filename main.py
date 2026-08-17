import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.requests_router import router as requests_router
from api.allocations_router import router as allocations_router
from api.agent_router import router as agent_router

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Housing Allocation System",
    description="AI-powered student housing allocation system",
    version="1.0.0"
)

# CORS middleware — allows frontend to talk to API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────

app.include_router(auth_router,        prefix="/api/v1")
app.include_router(requests_router,    prefix="/api/v1")
app.include_router(allocations_router, prefix="/api/v1")
app.include_router(agent_router,       prefix="/api/v1")


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "healthy",
        "message": "Housing Allocation System API",
        "version": "1.0.0",
        "docs":    "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status":    "healthy",
        "timestamp": "2026-06-08T00:00:00Z"
    }