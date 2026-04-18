# simulator/simpy/nodes.py
# Defines the Node class — represents a virtual compute node (server)

class Node:
    """
    Represents a single compute node in the simulated infrastructure.
    
    Each node has:
    - CPU capacity (max 100%)
    - RAM capacity (max in GB)
    - A queue of waiting workloads
    - Temperature (degrees Celsius)
    - Power draw (Watts)
    - Status (active, overloaded, idle, offline)
    """
    
    def __init__(self, node_id: str, cpu_capacity: float = 100.0, ram_capacity: float = 16.0):
        self.id = node_id
        self.type = "compute"  # can be: compute, storage, edge
        
        # Capacities
        self.cpu_capacity = cpu_capacity   # max CPU in percentage points
        self.ram_capacity = ram_capacity   # max RAM in GB
        
        # Current usage
        self.cpu_used = 0.0        # current CPU % in use
        self.ram_used = 0.0        # current RAM GB in use
        self.queue_length = 0      # number of waiting tasks
        
        # Physical state
        self.temperature = 35.0   # degrees Celsius, baseline idle temp
        self.power = 50.0         # Watts, baseline idle power
        
        # Status
        self.status = "active"    # active | overloaded | idle | offline
        
        # Active workloads currently running on this node
        self.active_workloads = []
    
    @property
    def cpu_free(self) -> float:
        """Returns available CPU percentage."""
        return max(0.0, self.cpu_capacity - self.cpu_used)
    
    @property
    def ram_free(self) -> float:
        """Returns available RAM in GB."""
        return max(0.0, self.ram_capacity - self.ram_used)
    
    @property
    def cpu_utilization(self) -> float:
        """Returns CPU usage as a 0.0-1.0 fraction."""
        return self.cpu_used / self.cpu_capacity if self.cpu_capacity > 0 else 0.0
    
    def update_status(self):
        """Recalculates node status based on current resource usage."""
        if self.cpu_utilization > 0.90 or self.ram_used / self.ram_capacity > 0.90:
            self.status = "overloaded"
        elif self.cpu_utilization < 0.05 and len(self.active_workloads) == 0:
            self.status = "idle"
        else:
            self.status = "active"
    
    def update_thermals(self):
        """
        Simulates temperature and power based on CPU load.
        Higher CPU usage = higher temperature and power draw.
        """
        # Temperature: ranges from 35°C (idle) to 85°C (100% CPU)
        self.temperature = 35.0 + (self.cpu_utilization * 50.0)
        
        # Add some randomness to make it realistic
        import random
        self.temperature += random.uniform(-1.0, 1.0)
        
        # Power: ranges from 50W (idle) to 250W (full load)
        self.power = 50.0 + (self.cpu_utilization * 200.0)
    
    def to_dict(self) -> dict:
        """Returns node state as a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "cpu_capacity": self.cpu_capacity,
            "cpu_used": round(self.cpu_used, 2),
            "cpu_free": round(self.cpu_free, 2),
            "cpu_utilization_pct": round(self.cpu_utilization * 100, 1),
            "ram_capacity": self.ram_capacity,
            "ram_used": round(self.ram_used, 2),
            "ram_free": round(self.ram_free, 2),
            "ram_utilization_pct": round((self.ram_used / self.ram_capacity) * 100, 1),
            "queue_length": self.queue_length,
            "temperature": round(self.temperature, 1),
            "power": round(self.power, 1),
            "status": self.status,
            "active_workload_count": len(self.active_workloads)
        }


