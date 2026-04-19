# simulator/mininet/topology.py
# Defines and starts the Mininet network topology

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
import random

def create_topology():
    """
    Creates a Mininet network that mirrors the SimPy compute nodes.
    
    Topology:
    
    h1 (node-1) ──┐
    h2 (node-2) ──┤
    h3 (node-3) ──┤── s1 (core switch) ── s2 (edge switch)
    h4 (node-4) ──┤
    h5 (node-5) ──┘
    
    Returns the Mininet net object.
    """
    setLogLevel("warning")  # Suppress verbose Mininet output
    
    net = Mininet(controller=OVSController, link=TCLink)
    
    # Add a controller
    net.addController("c0")
    
    # Add a core switch and an edge switch
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    
    # Add hosts — one per SimPy node
    hosts = []
    for i in range(1, 6):
        h = net.addHost(f"h{i}", ip=f"10.0.0.{i}/24")
        hosts.append(h)
    
    # Connect hosts to core switch s1
    # Each link has: bandwidth (Mbps), delay (ms), packet loss (%)
    net.addLink(hosts[0], s1, bw=1000, delay="1ms", loss=0)
    net.addLink(hosts[1], s1, bw=1000, delay="1ms", loss=0)
    net.addLink(hosts[2], s1, bw=500, delay="2ms", loss=0)
    net.addLink(hosts[3], s1, bw=500, delay="2ms", loss=0)
    net.addLink(hosts[4], s2, bw=100, delay="5ms", loss=0)
    
    # Connect core switch to edge switch
    net.addLink(s1, s2, bw=1000, delay="1ms", loss=0)
    
    return net, hosts, [s1, s2]
