# backend/routes/system.py
from fastapi import APIRouter, Depends, BackgroundTasks
from backend.auth.roles import get_current_user
from backend.services.state_service import get_unified_state
from backend.services.execution import run_control_loop, get_decision_history
from backend.adapters.simpy_adapter import trigger_scenario

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/state")
def get_state(current_user: dict = Depends(get_current_user)):
    """Returns the full unified system state."""
    return get_unified_state()

@router.get("/nodes")
def get_nodes(current_user: dict = Depends(get_current_user)):
    state = get_unified_state()
    return {"nodes": state["nodes"]}

@router.get("/workloads")
def get_workloads(current_user: dict = Depends(get_current_user)):
    state = get_unified_state()
    return {"workloads": state["workloads"]}

@router.get("/alerts")
def get_alerts(current_user: dict = Depends(get_current_user)):
    state = get_unified_state()
    return {"alerts": state["alerts"]}

@router.get("/decisions")
def get_decisions(current_user: dict = Depends(get_current_user)):
    return {"decisions": get_decision_history(limit=20)}

@router.get("/topology")
def get_topology(current_user: dict = Depends(get_current_user)):
    """Returns Mininet network topology."""
    from backend.adapters.mininet_adapter import get_topology
    return get_topology()

@router.post("/optimize")
def run_optimize(current_user: dict = Depends(get_current_user)):
    """Manually triggers the control loop optimization cycle."""
    state = get_unified_state()
    decisions = run_control_loop(state)
    return {"triggered": True, "decisions_made": len(decisions), "decisions": decisions}

@router.post("/scenario/{scenario_name}")
def trigger_scenario_endpoint(
    scenario_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Triggers a named simulation scenario (requires operator or admin role)."""
    if current_user["role"] not in ("operator", "admin"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Requires operator or admin role")
    trigger_scenario(scenario_name)
    return {"triggered": True, "scenario": scenario_name}
