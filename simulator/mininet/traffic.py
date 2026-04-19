# simulator/mininet/traffic.py
# Simulates traffic conditions between Mininet hosts

import subprocess
import random
import threading
import time

# ─────────────────────────────────────────────────────────────────
# Traffic state — updated by background thread, read by server
# ─────────────────────────────────────────────────────────────────

_traffic_state = {
    "links": [],
    "congestion_nodes": [],
    "last_updated": None,
}
_traffic_lock = threading.Lock()

# Node-to-host mapping (SimPy node ID → Mininet host IP)
NODE_HOST_MAP = {
    "node-1": "10.0.0.1",
    "node-2": "10.0.0.2",
    "node-3": "10.0.0.3",
    "node-4": "10.0.0.4",
    "node-5": "10.0.0.5",
}

def get_traffic_state() -> dict:
    """Returns the current traffic state (called by the Flask server)."""
    with _traffic_lock:
        return dict(_traffic_state)

def simulate_traffic_update(net, hosts):
    """
    Background thread function — continuously simulates traffic conditions.
    Updates _traffic_state every 2 seconds.
    """
    from datetime import datetime
    
    while True:
        links = []
        congestion_nodes = []
        
        for i, src_host in enumerate(hosts):
            for j, dst_host in enumerate(hosts):
                if i >= j:
                    continue  # avoid duplicates and self-links
                
                # Simulate measured latency (random, but influenced by load)
                base_delay = abs(i - j) * 1.5  # farther apart = higher base delay
                load_factor = random.uniform(0.8, 2.5)
                measured_delay_ms = round(base_delay * load_factor + random.uniform(0.1, 2.0), 2)
                
                # Simulate bandwidth utilization
                bandwidth_used_pct = random.uniform(5.0, 95.0)
                congested = bandwidth_used_pct > 80.0
                
                link_info = {
                    "source": f"node-{i+1}",
                    "target": f"node-{j+1}",
                    "source_ip": f"10.0.0.{i+1}",
                    "target_ip": f"10.0.0.{j+1}",
                    "delay_ms": measured_delay_ms,
                    "bandwidth_used_pct": round(bandwidth_used_pct, 1),
                    "congested": congested,
                    "status": "degraded" if congested else "healthy",
                }
                links.append(link_info)
                
                if congested:
                    for node_id in [f"node-{i+1}", f"node-{j+1}"]:
                        if node_id not in congestion_nodes:
                            congestion_nodes.append(node_id)
        
        with _traffic_lock:
            _traffic_state["links"] = links
            _traffic_state["congestion_nodes"] = congestion_nodes
            _traffic_state["last_updated"] = datetime.utcnow().isoformat()
        
        time.sleep(2)

def get_path_quality(source_node: str, target_node: str) -> dict:
    """
    Returns network quality information for a specific source→target path.
    Used by the backend when it needs to route a workload.
    """
    with _traffic_lock:
        for link in _traffic_state.get("links", []):
            if (link["source"] == source_node and link["target"] == target_node) or \
               (link["source"] == target_node and link["target"] == source_node):
                return {
                    "path_available": True,
                    "delay_ms": link["delay_ms"],
                    "congested": link["congested"],
                    "bandwidth_used_pct": link["bandwidth_used_pct"],
                    "recommendation": "avoid" if link["congested"] else "use",
                }
    
    return {
        "path_available": False,
        "delay_ms": None,
        "congested": True,
        "bandwidth_used_pct": 100.0,
        "recommendation": "avoid",
    }



