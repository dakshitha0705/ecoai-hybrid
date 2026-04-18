# simulator/simpy/engine.py
# Main SimPy simulation engine — runs in a background thread

import simpy
import threading
import time
import random
from simulator.simpy.nodes import Node
from simulator.simpy.workloads import Workload, WorkloadGenerator
from simulator.simpy import state as sim_state

# ─────────────────────────────────────────────────────────────────
# Scheduler — assigns workloads to nodes
# ─────────────────────────────────────────────────────────────────

class Scheduler:
    """
    Assigns incoming workloads to nodes using a simple best-fit algorithm.
    If no node can accept the workload, it enters the global pending queue.
    """
    
    def __init__(self, env: simpy.Environment, nodes: list):
        self.env = env
        self.nodes = nodes
        self.pending_queue = []   # workloads waiting for a free node
    
    def submit(self, workload: Workload):
        """Receives a new workload and tries to assign it."""
        node = self._find_best_node(workload)
        if node:
            self.env.process(self._run_workload(workload, node))
        else:
            # No node has capacity — add to pending queue
            workload.status = "queued"
            self.pending_queue.append(workload)
            node_to_queue = self._least_busy_node()
            if node_to_queue:
                node_to_queue.queue_length += 1
    
    def _find_best_node(self, workload: Workload):
        """Find the node with most free CPU that can fit this workload."""
        candidates = [
            n for n in self.nodes
            if n.cpu_free >= workload.cpu_required
            and n.ram_free >= workload.ram_required
            and n.status != "offline"
        ]
        if not candidates:
            return None
        # Sort by free CPU descending — pick the node with most headroom
        candidates.sort(key=lambda n: n.cpu_free, reverse=True)
        return candidates[0]
    
    def _least_busy_node(self):
        """Find the node with shortest queue for overflow."""
        active = [n for n in self.nodes if n.status != "offline"]
        if not active:
            return None
        return min(active, key=lambda n: n.queue_length)
    
    def _run_workload(self, workload: Workload, node: Node):
        """SimPy process: runs a workload on a node from start to completion."""
        from datetime import datetime
        
        # Assign workload to node
        workload.status = "running"
        workload.assigned_node = node.id
        workload.started_at = datetime.utcnow().isoformat()
        node.cpu_used = min(node.cpu_capacity, node.cpu_used + workload.cpu_required)
        node.ram_used = min(node.ram_capacity, node.ram_used + workload.ram_required)
        node.active_workloads.append(workload.id)
        
        # Register workload in global state
        sim_state.add_workload(workload)
        
        # Simulate work being done — yield for the duration
        yield self.env.timeout(workload.duration)
        
        # Workload complete — free resources
        workload.status = "complete"
        workload.completed_at = datetime.utcnow().isoformat()
        node.cpu_used = max(0.0, node.cpu_used - workload.cpu_required)
        node.ram_used = max(0.0, node.ram_used - workload.ram_required)
        if workload.id in node.active_workloads:
            node.active_workloads.remove(workload.id)
        
        # Update state
        sim_state.update_workload(workload)
        
        # Try to drain the pending queue
        self._drain_queue()
    
    def _drain_queue(self):
        """After a workload completes, try to assign pending tasks."""
        still_pending = []
        for workload in self.pending_queue:
            node = self._find_best_node(workload)
            if node:
                node.queue_length = max(0, node.queue_length - 1)
                self.env.process(self._run_workload(workload, node))
            else:
                still_pending.append(workload)
        self.pending_queue = still_pending

# ─────────────────────────────────────────────────────────────────
# State updater — runs every SimPy time unit
# ─────────────────────────────────────────────────────────────────

def state_updater(env: simpy.Environment, nodes: list):
    """
    Periodically updates node thermals, status, and pushes to global state.
    This runs as a SimPy process every 1 time unit (1 second).
    """
    while True:
        yield env.timeout(1)  # wait 1 simulated second
        for node in nodes:
            node.update_thermals()
            node.update_status()
        
        # Push updated node state to the shared state module
        sim_state.update_nodes(nodes)

# ─────────────────────────────────────────────────────────────────
# SimulationEngine — public interface
# ─────────────────────────────────────────────────────────────────

class SimulationEngine:
    """
    Main entry point for the SimPy simulation.
    Runs in a background thread so it doesn't block the FastAPI server.
    """
    
    def __init__(self):
        self.env = simpy.Environment()
        self.nodes = []
        self.scheduler = None
        self.generator = None
        self._thread = None
        self._running = False
    
    def setup(self):
        """Creates nodes, scheduler, generator, and registers SimPy processes."""
        # Create 5 compute nodes
        self.nodes = [
            Node("node-1", cpu_capacity=100.0, ram_capacity=16.0),
            Node("node-2", cpu_capacity=100.0, ram_capacity=16.0),
            Node("node-3", cpu_capacity=80.0, ram_capacity=8.0),
            Node("node-4", cpu_capacity=80.0, ram_capacity=8.0),
            Node("node-5", cpu_capacity=60.0, ram_capacity=4.0),
        ]
        
        # Initialize shared state with these nodes
        sim_state.initialize(self.nodes)
        
        # Create scheduler
        self.scheduler = Scheduler(self.env, self.nodes)
        
        # Create workload generator (starts in normal mode)
        self.generator = WorkloadGenerator(self.env, self.scheduler, mode="normal")
        
        # Register state updater process
        self.env.process(state_updater(self.env, self.nodes))
    
    def _run_forever(self):
        """Runs the SimPy simulation indefinitely (1 real second = 1 simulated second)."""
        self._running = True
        while self._running:
            self.env.step()  # advance one SimPy event
            time.sleep(0.01)  # small sleep to not peg the CPU
    
    def start(self):
        """Starts the simulation in a background thread."""
        self.setup()
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()
        print("[SimPy] Simulation engine started.")
    
    def stop(self):
        self._running = False
        print("[SimPy] Simulation engine stopped.")
    
    def trigger_scenario(self, scenario_name: str):
        """Triggers a pre-defined stress scenario."""
        from simulator.simpy.scenarios import apply_scenario
        apply_scenario(scenario_name, self.env, self.nodes, self.scheduler, self.generator)
    
    def get_state(self) -> dict:
        """Returns the current simulation state."""
        return sim_state.get_snapshot()
    
    def reassign_workload(self, workload_id: str, target_node_id: str) -> bool:
        """
        Called by the backend execution layer to reassign a workload.
        This simulates an override action.
        """
        return sim_state.reassign_workload(workload_id, target_node_id, self.nodes)

# Singleton instance — imported by the backend adapter
engine = SimulationEngine()

