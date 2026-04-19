# backend/services/state_service.py
# Merges SimPy and Mininet state into one unified model

import uuid
from datetime import datetime
from backend.adapters.simpy_adapter import get_simpy_state
from backend.adapters.mininet_adapter import get_topology, get_traffic

def get_unified_state() -> dict:
    """
    Reads from both SimPy and Mininet adapters and merges their data
    into a single unified state object.
    
    This is called by every frontend-facing route that needs system state.
    """
    # ── 1. Read SimPy ────────────────────────────────────────────
    simpy_data = get_simpy_state()
    
    # ── 2. Read Mininet ──────────────────────────────────────────
    traffic_data = get_traffic()
    topology_data = get_topology()
    
    network_available = not traffic_data.get("fallback", True)
    
    # ── 3. Build nodes from SimPy ─────────────────────────────────
    nodes = simpy_data.get("nodes", [])
    
    # Enrich nodes with network congestion info from Mininet
    congestion_nodes = traffic_data.get("congestion_nodes", [])
    for node in nodes:
        node["network_congested"] = node["id"] in congestion_nodes
    
    # ── 4. Build links from Mininet ───────────────────────────────
    links = traffic_data.get("links", [])
    
    # ── 5. Generate alerts based on state ─────────────────────────
    alerts = _generate_alerts(nodes, links, network_available)
    
    return {
        "nodes": nodes,
        "workloads": simpy_data.get("workloads", []),
        "links": links,
        "alerts": alerts,
        "network_available": network_available,
        "last_updated": datetime.utcnow().isoformat(),
    }

def _generate_alerts(nodes: list, links: list, network_available: bool) -> list:
    """Generates alert objects based on current state."""
    alerts = []
    
    # Node-level alerts
    for node in nodes:
        if node["status"] == "overloaded":
            alerts.append({
                "id": str(uuid.uuid4())[:8],
                "severity": "critical",
                "message": f"Node {node['id']} is overloaded — CPU {node['cpu_utilization_pct']}%",
                "source": "simpy",
                "node_id": node["id"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        elif node["status"] == "offline":
            alerts.append({
                "id": str(uuid.uuid4())[:8],
                "severity": "critical",
                "message": f"Node {node['id']} is OFFLINE",
                "source": "simpy",
                "node_id": node["id"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        elif node.get("network_congested"):
            alerts.append({
                "id": str(uuid.uuid4())[:8],
                "severity": "warning",
                "message": f"Node {node['id']} has network congestion",
                "source": "mininet",
                "node_id": node["id"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        elif node["queue_length"] > 5:
            alerts.append({
                "id": str(uuid.uuid4())[:8],
                "severity": "warning",
                "message": f"Node {node['id']} queue backing up — {node['queue_length']} tasks waiting",
                "source": "simpy",
                "node_id": node["id"],
                "timestamp": datetime.utcnow().isoformat(),
            })
    
    # Network-level alerts
    if not network_available:
        alerts.append({
            "id": str(uuid.uuid4())[:8],
            "severity": "warning",
            "message": "Mininet network layer is unreachable — network data unavailable",
            "source": "mininet",
            "node_id": None,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    return alerts



