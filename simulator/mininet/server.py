# simulator/mininet/server.py
# Flask HTTP server — exposes Mininet state to the FastAPI backend
# Run this in Ubuntu/WSL: sudo python3 server.py

import sys
import os
import threading
import time
from flask import Flask, jsonify
from flask_cors import CORS

# Add project root to path so imports work
sys.path.insert(0, "/mnt/c/Users/Dakshitha/ecoai/ecoai-hybrid")
# ↑ CHANGE THIS to your actual Windows path

from simulator.mininet.topology import create_topology
from simulator.mininet.traffic import simulate_traffic_update, get_traffic_state

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the FastAPI backend

# ─────────────────────────────────────────────────────────────────
# Global state
# ─────────────────────────────────────────────────────────────────

_net = None
_hosts = None
_switches = None
_started = False

def start_mininet():
    """Starts Mininet and the traffic simulation background thread."""
    global _net, _hosts, _switches, _started
    
    print("[Mininet Server] Starting Mininet topology...")
    _net, _hosts, _switches = create_topology()
    _net.start()
    _started = True
    print("[Mininet Server] Mininet started. Hosts:", [h.name for h in _hosts])
    
    # Start traffic simulation in background thread
    traffic_thread = threading.Thread(
        target=simulate_traffic_update,
        args=(_net, _hosts),
        daemon=True
    )
    traffic_thread.start()
    print("[Mininet Server] Traffic simulation running.")

# ─────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────

@app.route("/topology", methods=["GET"])
def get_topology():
    """
    Returns the network topology: nodes (hosts) and links.
    
    Sample response:
    {
      "nodes": [
        {"id": "node-1", "host": "h1", "ip": "10.0.0.1", "switch": "s1"},
        ...
      ],
      "switches": [
        {"id": "s1", "type": "core"},
        {"id": "s2", "type": "edge"}
      ],
      "links": [
        {"source": "node-1", "target": "s1", "bandwidth_mbps": 1000, "delay_ms": 1},
        ...
      ]
    }
    """
    if not _started:
        return jsonify({"error": "Mininet not started yet"}), 503
    
    nodes = []
    for i, h in enumerate(_hosts):
        node_id = f"node-{i+1}"
        switch_name = "s1" if i < 4 else "s2"
        nodes.append({
            "id": node_id,
            "host": h.name,
            "ip": h.IP(),
            "switch": switch_name,
        })
    
    switches = [
        {"id": "s1", "type": "core"},
        {"id": "s2", "type": "edge"},
    ]
    
    # Static link definitions matching what create_topology() set up
    links = [
        {"source": "node-1", "target": "s1", "bandwidth_mbps": 1000, "delay_ms": 1},
        {"source": "node-2", "target": "s1", "bandwidth_mbps": 1000, "delay_ms": 1},
        {"source": "node-3", "target": "s1", "bandwidth_mbps": 500, "delay_ms": 2},
        {"source": "node-4", "target": "s1", "bandwidth_mbps": 500, "delay_ms": 2},
        {"source": "node-5", "target": "s2", "bandwidth_mbps": 100, "delay_ms": 5},
        {"source": "s1", "target": "s2", "bandwidth_mbps": 1000, "delay_ms": 1},
    ]
    
    return jsonify({
        "nodes": nodes,
        "switches": switches,
        "links": links,
        "status": "running",
    })

@app.route("/traffic", methods=["GET"])
def get_traffic():
    """
    Returns current traffic conditions between nodes.
    
    Sample response:
    {
      "links": [
        {
          "source": "node-1",
          "target": "node-2",
          "delay_ms": 2.3,
          "bandwidth_used_pct": 45.2,
          "congested": false,
          "status": "healthy"
        },
        ...
      ],
      "congestion_nodes": [],
      "last_updated": "2024-01-01T12:00:00"
    }
    """
    if not _started:
        return jsonify({"error": "Mininet not started yet"}), 503
    
    return jsonify(get_traffic_state())

@app.route("/status", methods=["GET"])
def get_status():
    """
    Returns basic server health status.
    Used by the backend adapter to check if Mininet is reachable.
    
    Sample response:
    {
      "status": "running",
      "host_count": 5,
      "switch_count": 2
    }
    """
    if not _started:
        return jsonify({"status": "starting", "host_count": 0, "switch_count": 0})
    
    return jsonify({
        "status": "running",
        "host_count": len(_hosts) if _hosts else 0,
        "switch_count": len(_switches) if _switches else 0,
    })

@app.route("/path", methods=["GET"])
def get_path():
    """
    Returns path quality between two specific nodes.
    Query params: source=node-1&target=node-2
    
    Used by backend when deciding if a workload can be migrated.
    """
    from flask import request
    from simulator.mininet.traffic import get_path_quality
    
    source = request.args.get("source", "node-1")
    target = request.args.get("target", "node-2")
    
    result = get_path_quality(source, target)
    return jsonify(result)

# ─────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────

import atexit

@atexit.register
def cleanup():
    global _net
    if _net:
        print("[Mininet Server] Cleaning up Mininet...")
        _net.stop()

# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start Mininet in main thread first
    start_mininet()
    
    # Then start Flask server
    print("[Mininet Server] Starting Flask server on port 9000...")
    app.run(host="0.0.0.0", port=9000, debug=False)
