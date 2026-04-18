# simulator/simpy/state.py
# Global shared state — updated by SimPy, read by the backend adapter
# Uses a threading.Lock to prevent race conditions

import threading
from datetime import datetime

_lock = threading.Lock()

# ─────────────────────────────────────────────────────────────────
# Internal state storage
# ─────────────────────────────────────────────────────────────────

_state = {
    "nodes": [],          # list of node dicts
    "workloads": {},      # dict of workload_id -> workload dict
    "last_updated": None,
}

def initialize(nodes):
    """Called once at startup with the list of Node objects."""
    with _lock:
        _state["nodes"] = [n.to_dict() for n in nodes]
        _state["last_updated"] = datetime.utcnow().isoformat()

def update_nodes(nodes):
    """Called by state_updater every SimPy tick to refresh node data."""
    with _lock:
        _state["nodes"] = [n.to_dict() for n in nodes]
        _state["last_updated"] = datetime.utcnow().isoformat()

def add_workload(workload):
    """Registers a new workload in the state."""
    with _lock:
        _state["workloads"][workload.id] = workload.to_dict()

def update_workload(workload):
    """Updates the state of an existing workload (e.g., when it completes)."""
    with _lock:
        if workload.id in _state["workloads"]:
            _state["workloads"][workload.id] = workload.to_dict()

def get_snapshot() -> dict:
    """Returns a deep copy of the current state (safe to return as JSON)."""
    with _lock:
        # Return only recent workloads to avoid unbounded growth
        recent_workloads = dict(
            sorted(
                _state["workloads"].items(),
                key=lambda item: item[1].get("queued_at", ""),
                reverse=True
            )[:50]  # last 50 workloads
        )
        return {
            "nodes": list(_state["nodes"]),
            "workloads": list(recent_workloads.values()),
            "last_updated": _state["last_updated"],
        }

def reassign_workload(workload_id: str, target_node_id: str, nodes: list) -> bool:
    """
    Attempts to reassign a queued workload to a specific node.
    Used by the backend execution layer for manual overrides.
    Returns True if successful.
    """
    with _lock:
        if workload_id not in _state["workloads"]:
            return False
        wl = _state["workloads"][workload_id]
        if wl["status"] != "queued":
            return False
        # Update assignment in state
        _state["workloads"][workload_id]["assigned_node"] = target_node_id
        _state["workloads"][workload_id]["status"] = "reassigned"
        return True
