# backend/services/detection.py
# Detects issues in the unified system state

def detect_issues(state: dict) -> list:
    """
    Analyzes the unified state and returns a list of detected issues.
    Each issue is a dict describing what was found and where.
    """
    issues = []
    nodes = state.get("nodes", [])
    links = state.get("links", [])
    
    for node in nodes:
        # ── Compute overload ─────────────────────────────────────
        if node.get("cpu_utilization_pct", 0) > 85:
            issues.append({
                "type": "compute_overload",
                "severity": "critical",
                "node_id": node["id"],
                "detail": f"CPU at {node['cpu_utilization_pct']}%",
            })
        
        # ── Memory pressure ───────────────────────────────────────
        if node.get("ram_utilization_pct", 0) > 90:
            issues.append({
                "type": "memory_pressure",
                "severity": "critical",
                "node_id": node["id"],
                "detail": f"RAM at {node['ram_utilization_pct']}%",
            })
        
        # ── Queue buildup ─────────────────────────────────────────
        if node.get("queue_length", 0) > 10:
            issues.append({
                "type": "queue_overflow",
                "severity": "warning",
                "node_id": node["id"],
                "detail": f"Queue length: {node['queue_length']}",
            })
        
        # ── Idle waste ────────────────────────────────────────────
        if node.get("cpu_utilization_pct", 100) < 5 and node.get("status") == "idle":
            issues.append({
                "type": "idle_node",
                "severity": "info",
                "node_id": node["id"],
                "detail": "Node is idle while others may be overloaded",
            })
        
        # ── Thermal alert ─────────────────────────────────────────
        if node.get("temperature", 0) > 80:
            issues.append({
                "type": "thermal_warning",
                "severity": "warning",
                "node_id": node["id"],
                "detail": f"Temperature at {node['temperature']}°C",
            })
    
    # ── Network congestion ────────────────────────────────────────
    for link in links:
        if link.get("congested"):
            issues.append({
                "type": "network_congestion",
                "severity": "warning",
                "node_id": link["source"],
                "detail": f"Link {link['source']}→{link['target']} congested at {link.get('bandwidth_used_pct')}%",
            })
    
    return issues
 
