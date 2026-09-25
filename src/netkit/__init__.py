"""netkit: IPv4 addressing and routing, implemented with integer arithmetic."""

from .ipv4 import IPv4Network, ip_to_int, int_to_ip, mask_from_prefix, prefix_from_mask, address_class
from .subnetting import split, vlsm, summarize
from .routing import RoutingTable, dijkstra, link_state_tables

__version__ = "0.1.0"
