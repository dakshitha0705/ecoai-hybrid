# simulator/simpy/scenarios.py
# Pre-built scenarios for demo and testing

import simpy
import random
from simulator.simpy.workloads import Workload

def apply_scenario(scenario_name: str, env, nodes, scheduler, generator):
    """
    Applies a named scenario to the simulation.
    This is called by the backend when a scenario is triggered via API.
    """
    if scenario_name == "compute_overload":
        _scenario_compute_overload(env, nodes, scheduler, generator)
    elif scenario_name == "memory_pressure":
        _scenario_memory_pressure(env, scheduler)
    elif scenario_name == "idle_imbalance":
        _scenario_idle_imbalance(env, nodes)
    elif scenario_name == "node_offline":
        _scenario_node_offline(nodes)
    else:
        print(f"[Scenarios] Unknown scenario: {scenario_name}")

def _scenario_compute_overload(env, nodes, scheduler, generator):
    """
    Floods the system with high-priority tasks to cause CPU overload.
    Also switches the generator to burst mode for 30 seconds.
    """
    print("[Scenario] compute_overload triggered")
    generator.switch_to_burst()
    
    # Inject 30 immediate high-priority batch jobs
    for _ in range(30):
        wl = Workload(workload_type="batch_job", priority=1)
        scheduler.submit(wl)
    
    # Schedule return to normal after 30 seconds
    def revert(env):
        yield env.timeout(30)
        generator.switch_to_normal()
        print("[Scenario] compute_overload resolved — back to normal")
    
    env.process(revert(env))

def _scenario_memory_pressure(env, scheduler):
    """
    Submits many memory-heavy tasks (data_pipeline, ml_inference) to exhaust RAM.
    """
    print("[Scenario] memory_pressure triggered")
    for _ in range(20):
        wl = Workload(workload_type=random.choice(["data_pipeline", "ml_inference"]), priority=2)
        wl.ram_required = random.uniform(4.0, 8.0)  # force high RAM usage
        scheduler.submit(wl)

def _scenario_idle_imbalance(env, nodes):
    """
    Forces some nodes to offline status to create load imbalance.
    """
    print("[Scenario] idle_imbalance triggered")
    if len(nodes) >= 4:
        nodes[2].status = "idle"  # force node-3 idle
        nodes[3].status = "idle"  # force node-4 idle
    
    # Revert after 20 seconds
    def revert(env):
        yield env.timeout(20)
        for n in nodes:
            if n.status == "idle" and len(n.active_workloads) == 0:
                n.status = "active"
        print("[Scenario] idle_imbalance resolved")
    
    env.process(revert(env))

def _scenario_node_offline(nodes):
    """Takes the highest-load node offline to simulate hardware failure."""
    print("[Scenario] node_offline triggered")
    if nodes:
        # Pick the node with most active workloads
        target = max(nodes, key=lambda n: len(n.active_workloads))
        target.status = "offline"
        print(f"[Scenario] Node {target.id} taken offline")
