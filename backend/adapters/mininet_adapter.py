# backend/adapters/mininet_adapter.py
# HTTP client for the Mininet Flask server running in WSL on port 9000

import requests
from datetime import datetime
from backend.config import MININET_BASE_URL, MININET_TIMEOUT_SECONDS

# ─────────────────────────────────────────────────────────────────
# Fallback responses (used when Mininet is unreachable)
# ─────────────────────────────────────────────────────────────────

_FALLBACK_TOPOLOGY = {
    "available": False,
    "fallback": True,
    "message": "Mininet server unreachable. Network data unavailable.",
    "nodes": [],
    "switches": [],
    "links": [],
}

_FALLBACK_TRAFFIC = {
    "available": False,
    "fallback": True,
    "message": "Mininet server unreachable. Traffic data unavailable.",
    "links": [],
    "congestion_nodes": [],
    "last_updated": None,
}

_FALLBACK_PATH = {
    "path_available": False,
    "delay_ms": None,
    "congested": True,
    "bandwidth_used_pct": 100.0,
    "recommendation": "avoid",
    "fallback": True,
    "message": "Mininet unreachable — cannot verify path quality.",
}

def _get(endpoint: str, params: dict = None) -> dict:
    """
    Internal helper: makes a GET request to the Mininet server.
    Returns parsed JSON dict, or None on any error.
    """
    url = f"{MININET_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=MININET_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"[Mininet Adapter] Connection error — is the Mininet server running on port 9000?")
        return None
    except requests.exceptions.Timeout:
        print(f"[Mininet Adapter] Timeout calling {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[Mininet Adapter] HTTP error {e.response.status_code} from {url}")
        return None
    except Exception as e:
        print(f"[Mininet Adapter] Unexpected error: {e}")
        return None

def is_available() -> bool:
    """Checks if the Mininet server is reachable."""
    result = _get("/status")
    return result is not None and result.get("status") == "running"

def get_topology() -> dict:
    """Returns the Mininet network topology."""
    result = _get("/topology")
    if result is None:
        return _FALLBACK_TOPOLOGY
    result["available"] = True
    result["fallback"] = False
    return result

def get_traffic() -> dict:
    """Returns current traffic/congestion state from Mininet."""
    result = _get("/traffic")
    if result is None:
        return _FALLBACK_TRAFFIC
    result["available"] = True
    result["fallback"] = False
    return result

def check_path(source_node: str, target_node: str) -> dict:
    """
    Checks the network path quality between two nodes.
    Called by the execution layer before migrating a workload.
    """
    result = _get("/path", params={"source": source_node, "target": target_node})
    if result is None:
        return _FALLBACK_PATH
    result["fallback"] = False
    return result
