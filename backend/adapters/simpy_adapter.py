# backend/adapters/simpy_adapter.py
# Reads from the SimPy engine — same Python process, direct import

from simulator.simpy.engine import engine as simpy_engine

def get_simpy_state() -> dict:
    """
    Returns the current SimPy simulation state.
    Contains: nodes, workloads, last_updated
    """
    return simpy_engine.get_state()

def trigger_scenario(scenario_name: str):
    """Triggers a named simulation scenario."""
    simpy_engine.trigger_scenario(scenario_name)

def reassign_workload(workload_id: str, target_node_id: str) -> bool:
    """
    Attempts to reassign a queued workload to a specific node.
    Returns True if successful.
    """
    return simpy_engine.reassign_workload(workload_id, target_node_id)

def force_node_offline(node_id: str) -> bool:
    """Forces a specific node offline in the simulation."""
    state = simpy_engine.get_state()
    for node in simpy_engine.nodes:
        if node.id == node_id:
            node.status = "offline"
            return True
    return False

def drain_node_queue(node_id: str) -> int:
    """
    Marks all queued workloads on a node as pending reassignment.
    Returns number of workloads affected.
    """
    from simulator.simpy import state as sim_state
    snapshot = sim_state.get_snapshot()
    count = 0
    for wl in snapshot["workloads"]:
        if wl.get("assigned_node") == node_id and wl.get("status") == "queued":
            sim_state.reassign_workload(wl["id"], None, simpy_engine.nodes)
            count += 1
    return count
