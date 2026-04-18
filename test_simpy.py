import sys
sys.path.insert(0, ".")

from simulator.simpy.engine import engine
import time

print("Starting simulation...")
engine.start()

time.sleep(5)

state = engine.get_state()
print(f"\nNodes ({len(state['nodes'])}):")
for node in state['nodes']:
    print(f"  {node['id']}: CPU={node['cpu_utilization_pct']}% RAM={node['ram_used']}GB status={node['status']}")

print(f"\nRecent workloads ({len(state['workloads'])}):")
for wl in state['workloads'][:5]:
    print(f"  {wl['id']} ({wl['type']}) -> {wl['status']} on {wl['assigned_node']}")

engine.stop()
print("\nDone.")