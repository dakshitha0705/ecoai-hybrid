# backend/services/decision.py
# Maps detected issues to concrete actions

import uuid
from datetime import datetime
from backend.adapters.mininet_adapter import check_path

def decide_actions(issues: list, state: dict) -> list:
    """
    Given a list of issues and current state, returns a list of decisions.
    Each decision includes: what action to take, on which node, and where to redirect.
    """
    decisions = []
    nodes = state.get("nodes", [])
    
    # Build a lookup of nodes sorted by free CPU (best candidates for receiving work)
    healthy_nodes = sorted(
        [n for n in nodes if n["status"] not in ("offline", "overloaded")],
        key=lambda n: n.get("cpu_utilization_pct", 100)
    )
    
    processed_nodes = set()
    
    for issue in issues:
        node_id = issue.get("node_id")
        issue_type = issue.get("type")
        
        # ── Compute overload: reassign workloads ──────────────────
        if issue_type in ("compute_overload", "queue_overflow") and node_id not in processed_nodes:
            target = _find_best_target(node_id, healthy_nodes, state)
            if target:
                decisions.append({
                    "id": str(uuid.uuid4())[:8],
                    "issue": issue_type,
                    "action": "reassign_workloads",
                    "affected_node": node_id,
                    "target_node": target["id"],
                    "result": "pending",
                    "timestamp": datetime.utcnow().isoformat(),
                    "auto": True,
                })
                processed_nodes.add(node_id)
        
        # ── Memory pressure: drain non-critical workloads ─────────
        elif issue_type == "memory_pressure" and node_id not in processed_nodes:
            decisions.append({
                "id": str(uuid.uuid4())[:8],
                "issue": issue_type,
                "action": "drain_low_priority_workloads",
                "affected_node": node_id,
                "target_node": None,
                "result": "pending",
                "timestamp": datetime.utcnow().isoformat(),
                "auto": True,
            })
            processed_nodes.add(node_id)
        
        # ── Network congestion: flag the node for routing avoidance
        elif issue_type == "network_congestion" and node_id not in processed_nodes:
            decisions.append({
                "id": str(uuid.uuid4())[:8],
                "issue": issue_type,
                "action": "avoid_congested_path",
                "affected_node": node_id,
                "target_node": None,
                "result": "flagged",
                "timestamp": datetime.utcnow().isoformat(),
                "auto": True,
            })
    
    return decisions

def _find_best_target(source_node: str, healthy_nodes: list, state: dict):
    """
    Finds the best destination node for workload migration.
    Checks network path quality via Mininet before recommending.
    """
    for candidate in healthy_nodes:
        if candidate["id"] == source_node:
            continue
        
        # Check network path before recommending
        path = check_path(source_node, candidate["id"])
        if not path.get("congested", True) and path.get("path_available", False):
            return candidate
    
    # If no ideal candidate found, return the least-loaded node anyway
    return healthy_nodes[0] if healthy_nodes else None
