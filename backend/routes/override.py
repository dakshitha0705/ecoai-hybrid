# backend/routes/override.py
from fastapi import APIRouter, Depends, HTTPException
from backend.models.schemas import OverrideRequest
from backend.auth.roles import get_current_user, require_role
from backend.auth.jwt_handler import authenticate_user
from backend.adapters.simpy_adapter import reassign_workload, force_node_offline, drain_node_queue
from backend.services.audit_store import write as audit_write

router = APIRouter(prefix="/override", tags=["override"])

require_operator = require_role(["operator", "admin"])

@router.post("/execute")
def execute_override(
    request: OverrideRequest,
    current_user: dict = Depends(require_operator)
):
    """
    Executes a manual override action.
    Requires re-authentication (user must provide their password again).
    """
    # Re-authenticate user before allowing override
    user = authenticate_user(current_user["username"], request.reauth_password)
    if not user:
        raise HTTPException(status_code=401, detail="Re-authentication failed — wrong password")
    
    result = "failed"
    
    if request.action == "reassign":
        success = reassign_workload(request.target, request.destination or "")
        result = "success" if success else "workload_not_found_or_not_queued"
    
    elif request.action == "force_offline":
        success = force_node_offline(request.target)
        result = "success" if success else "node_not_found"
    
    elif request.action == "drain_queue":
        count = drain_node_queue(request.target)
        result = f"drained_{count}_workloads"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown override action: {request.action}")
    
    # Log the override action
    log_entry = audit_write(
        user=current_user["username"],
        role=current_user["role"],
        action=request.action,
        target=request.target,
        reason=request.reason,
        result=result,
        auto=False,
    )
    
    return {"result": result, "audit_id": log_entry["id"]}
