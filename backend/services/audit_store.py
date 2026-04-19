
# backend/services/audit_store.py
# Simple in-memory audit log — swap for SQLite in production

import uuid
from datetime import datetime
from threading import Lock

_log = []
_lock = Lock()

def write(user: str, role: str, action: str, target: str, reason: str, result: str, auto: bool = False):
    """Appends a new audit log entry."""
    entry = {
        "id": str(uuid.uuid4())[:8],
        "user": user,
        "role": role,
        "action": action,
        "target": target,
        "reason": reason,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
        "auto": auto,
    }
    with _lock:
        _log.append(entry)
    return entry

def read(limit: int = 100) -> list:
    """Returns the most recent audit log entries."""
    with _lock:
        return list(reversed(_log[-limit:]))
