# backend/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class NodeSchema(BaseModel):
    id: str
    type: str
    cpu_utilization_pct: float
    ram_utilization_pct: float
    cpu_used: float
    ram_used: float
    queue_length: int
    temperature: float
    power: float
    status: str

class WorkloadSchema(BaseModel):
    id: str
    type: str
    priority: int
    cpu_required: float
    ram_required: float
    status: str
    assigned_node: Optional[str] = None
    queued_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class LinkSchema(BaseModel):
    source: str
    target: str
    delay_ms: Optional[float] = None
    bandwidth_used_pct: Optional[float] = None
    congested: bool = False
    status: str = "unknown"

class AlertSchema(BaseModel):
    id: str
    severity: str   # critical | warning | info
    message: str
    source: str     # simpy | mininet | hybrid
    node_id: Optional[str] = None
    timestamp: str

class DecisionSchema(BaseModel):
    id: str
    issue: str
    action: str
    affected_node: Optional[str] = None
    target_node: Optional[str] = None
    result: str
    timestamp: str
    auto: bool = True

class UnifiedStateSchema(BaseModel):
    nodes: List[NodeSchema]
    workloads: List[WorkloadSchema]
    links: List[LinkSchema]
    alerts: List[AlertSchema]
    decisions: List[DecisionSchema]
    network_available: bool
    last_updated: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class OverrideRequest(BaseModel):
    action: str           # reassign | cancel_workload | force_offline | drain_queue
    target: str           # node ID or workload ID
    destination: Optional[str] = None  # for reassign: target node
    reason: str
    reauth_password: str  # requires re-authentication

class AuditLogEntry(BaseModel):
    id: str
    user: str
    role: str
    action: str
    target: str
    reason: str
    result: str
    timestamp: str
    auto: bool = False
