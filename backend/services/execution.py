# backend/services/execution.py
# Applies decisions — modifies SimPy state, optionally queries Mininet

import uuid
from datetime import datetime
from backend.adapters.simpy_adapter import (
    reassign_workload, force_node_offline, drain_node_queue
)
from backend.adapters.mininet_adapter import check_path

_decision_history = []  # In-memory log — replace with DB in production

def execute_decision(decision: dict, state: dict) -> dict:
    """
    Executes a single decision from the decision layer.
    Returns the updated decision with result filled in.
    """
    action = decision.get("action")
    affected_node = decision.get("affected_node")
    target_node = decision.get("target_node")
    
    result = "failed"
    workloads_moved = 0
    
    if action == "reassign_workloads":
        workloads_moved = _do_reassign(affected_node, target_node, state)
        result = "success" if workloads_moved > 0 else "no_workloads_to_move"
    
    elif action == "drain_low_priority_workloads":
        count = drain_node_queue(affected_node)
        result = f"drained_{count}_workloads"
        workloads_moved = count
    
    elif action == "avoid_congested_path":
        result = "flagged"  # This is informational — no direct SimPy modification
    
    elif action == "force_offline":
        success = force_node_offline(affected_node)
        result = "success" if success else "node_not_found"
    
    # Update decision record
    decision["result"] = result
    decision["workloads_moved"] = workloads_moved
    decision["executed_at"] = datetime.utcnow().isoformat()
    
    # Log to in-memory history
    _decision_history.append(dict(decision))
    
    return decision

def _do_reassign(source_node: str, target_node: str, state: dict) -> int:
    """
    Finds queued workloads on source_node and reassigns them to target_node.
    Returns number of workloads successfully moved.
    """
    workloads = state.get("workloads", [])
    queued_on_source = [
        wl for wl in workloads
        if wl.get("assigned_node") == source_node and wl.get("status") == "queued"
    ]
    
    moved = 0
    for wl in queued_on_source[:5]:  # move up to 5 at a time
        success = reassign_workload(wl["id"], target_node)
        if success:
            moved += 1
    
    return moved

def get_decision_history(limit: int = 50) -> list:
    """Returns recent decision history."""
    return _decision_history[-limit:]

def run_control_loop(state: dict) -> list:
    """
    Top-level function called periodically by a background task.
    Detects issues → decides actions → executes them.
    Returns list of executed decisions.
    """
    from backend.services.detection import detect_issues
    from backend.services.decision import decide_actions
    
    issues = detect_issues(state)
    if not issues:
        return []
    
    decisions = decide_actions(issues, state)
    executed = []
    for decision in decisions:
        result = execute_decision(decision, state)
        executed.append(result)
    
    return executed
