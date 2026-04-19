# backend/routes/audit.py
from fastapi import APIRouter, Depends
from backend.auth.roles import get_current_user
from backend.services.audit_store import read as audit_read

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs")
def get_audit_logs(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Returns audit log entries. Any authenticated user can view logs."""
    return {"logs": audit_read(limit=limit)}
