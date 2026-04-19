# backend/main.py
# FastAPI application entry point

import sys
import os

# Add project root to Python path so 'simulator' package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from backend.routes.auth import router as auth_router
from backend.routes.system import router as system_router
from backend.routes.override import router as override_router
from backend.routes.audit import router as audit_router

# ─────────────────────────────────────────────────────────────────
# Start SimPy on startup
# ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts SimPy simulation engine when the FastAPI server starts."""
    from simulator.simpy.engine import engine
    print("[EcoAI Backend] Starting SimPy simulation engine...")
    engine.start()
    
    # Start background control loop
    asyncio.create_task(background_control_loop())
    
    yield  # Application runs here
    
    print("[EcoAI Backend] Shutting down SimPy engine...")
    engine.stop()

async def background_control_loop():
    """Runs the EcoAI control loop every 5 seconds in the background."""
    from backend.services.state_service import get_unified_state
    from backend.services.execution import run_control_loop
    
    while True:
        await asyncio.sleep(5)
        try:
            state = get_unified_state()
            decisions = run_control_loop(state)
            if decisions:
                print(f"[Control Loop] Made {len(decisions)} decisions")
        except Exception as e:
            print(f"[Control Loop] Error: {e}")

# ─────────────────────────────────────────────────────────────────
# Create FastAPI app
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="EcoAI Backend",
    description="Hybrid SimPy + Mininet control-plane system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allows the React frontend (on port 3000) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(system_router)
app.include_router(override_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {"status": "EcoAI Backend running", "docs": "/docs"}
