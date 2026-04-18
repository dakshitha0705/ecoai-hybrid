# simulator/simpy/workloads.py
# Defines Workload class and WorkloadGenerator

import simpy
import random
import uuid
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# Workload class
# ─────────────────────────────────────────────────────────────────

class Workload:
    """
    Represents a single compute task/job in the simulation.
    
    Priority levels:
    - 1 = critical (must run immediately)
    - 2 = high
    - 3 = normal
    - 4 = low (can be delayed)
    """
    
    TYPES = ["web_request", "batch_job", "data_pipeline", "ml_inference", "health_check"]
    
    def __init__(self, workload_id: str = None, workload_type: str = None, priority: int = 3):
        self.id = workload_id or str(uuid.uuid4())[:8]
        self.type = workload_type or random.choice(self.TYPES)
        self.priority = priority
        
        # Resource requirements (set based on type)
        self.cpu_required = self._cpu_for_type()
        self.ram_required = self._ram_for_type()
        self.duration = self._duration_for_type()  # in SimPy time units
        
        # State tracking
        self.status = "queued"    # queued | running | complete | failed
        self.assigned_node = None
        self.queued_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None
    
    def _cpu_for_type(self) -> float:
        mapping = {
            "web_request": random.uniform(2.0, 8.0),
            "batch_job": random.uniform(15.0, 35.0),
            "data_pipeline": random.uniform(20.0, 50.0),
            "ml_inference": random.uniform(30.0, 60.0),
            "health_check": random.uniform(0.5, 2.0),
        }
        return mapping.get(self.type, 10.0)
    
    def _ram_for_type(self) -> float:
        mapping = {
            "web_request": random.uniform(0.1, 0.5),
            "batch_job": random.uniform(1.0, 4.0),
            "data_pipeline": random.uniform(2.0, 6.0),
            "ml_inference": random.uniform(3.0, 8.0),
            "health_check": random.uniform(0.05, 0.1),
        }
        return mapping.get(self.type, 1.0)
    
    def _duration_for_type(self) -> float:
        """Duration in SimPy time units (we treat 1 unit = 1 second)."""
        mapping = {
            "web_request": random.uniform(1.0, 5.0),
            "batch_job": random.uniform(10.0, 30.0),
            "data_pipeline": random.uniform(15.0, 45.0),
            "ml_inference": random.uniform(5.0, 20.0),
            "health_check": random.uniform(0.5, 1.0),
        }
        return mapping.get(self.type, 5.0)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "priority": self.priority,
            "cpu_required": round(self.cpu_required, 2),
            "ram_required": round(self.ram_required, 2),
            "duration": round(self.duration, 2),
            "status": self.status,
            "assigned_node": self.assigned_node,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

# ─────────────────────────────────────────────────────────────────
# WorkloadGenerator — runs inside SimPy environment
# ─────────────────────────────────────────────────────────────────

class WorkloadGenerator:
    """
    Continuously generates workloads and submits them to the scheduler.
    
    Modes:
    - normal: steady stream of tasks
    - burst: sudden spike in task arrivals
    """
    
    def __init__(self, env: simpy.Environment, scheduler, mode: str = "normal"):
        self.env = env
        self.scheduler = scheduler
        self.mode = mode
        self.generated_count = 0
        
        # Start generating
        self.env.process(self.run())
    
    def run(self):
        """Main generator loop — runs for the life of the simulation."""
        while True:
            # Determine how long to wait before next workload arrives
            if self.mode == "normal":
                inter_arrival = random.expovariate(1.0 / 3.0)  # avg 3 seconds between tasks
            elif self.mode == "burst":
                inter_arrival = random.expovariate(1.0 / 0.3)  # avg 0.3 seconds — 10x faster
            else:
                inter_arrival = 3.0
            
            yield self.env.timeout(inter_arrival)
            
            # Create a new workload with random priority
            priority = random.choices([1, 2, 3, 4], weights=[5, 20, 60, 15])[0]
            workload = Workload(priority=priority)
            self.generated_count += 1
            
            # Hand it to the scheduler
            self.scheduler.submit(workload)
    
    def switch_to_burst(self):
        self.mode = "burst"
    
    def switch_to_normal(self):
        self.mode = "normal"




