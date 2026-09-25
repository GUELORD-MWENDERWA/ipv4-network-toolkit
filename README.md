# netkit: IPv4 Addressing and Routing Toolkit

![tests](https://github.com/GUELORD-MWENDERWA/ipv4-network-toolkit/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![license](https://img.shields.io/badge/license-MIT-green)

A dependency-free toolkit for IPv4 network design: address and mask arithmetic, equal-size subnetting, VLSM allocation, route summarisation, longest-prefix-match forwarding and link-state (OSPF-style) shortest-path routing.

Addresses are manipulated as 32-bit integers with explicit bit operations (`network = ip & mask`, `broadcast = network | ~mask`), which makes the code a readable companion to a first computer networks course. Results are cross-checked against Python's `ipaddress` module on randomised inputs.

## Features

| Area | What it does |
| --- | --- |
| Addressing | Parse CIDR or dotted masks, network and broadcast addresses, wildcard mask, host range, usable hosts (including /31 and /32), address class, private range detection |
| Subnetting | Split a block into equal subnets by prefix or by required count |
| VLSM | Allocate subnets for named host requirements, largest first, aligned, with overflow detection |
| Summarisation | Smallest covering supernet for a set of routes |
| Forwarding | Routing table with longest-prefix match and default route |
| Link-state routing | Dijkstra shortest paths and per-router forwarding tables (first hop and cost) |

## Installation

```bash
git clone https://github.com/GUELORD-MWENDERWA/ipv4-network-toolkit.git
cd ipv4-network-toolkit
pip install -e ".[dev]"
```

## Command line

```console
$ netkit info 192.168.10.77/26
network       192.168.10.64/26
mask          255.255.255.192
wildcard      0.0.0.63
broadcast     192.168.10.127
first_host    192.168.10.65
last_host     192.168.10.126
usable_hosts  62
class         C
private       True

$ netkit vlsm 192.168.1.0/24 LAN_A=100 LAN_B=50 LAN_C=20 WAN1=2 WAN2=2
name       network            mask            host range                         hosts
LAN_A      192.168.1.0/25     255.255.255.128 192.168.1.1 - 192.168.1.126          126
LAN_B      192.168.1.128/26   255.255.255.192 192.168.1.129 - 192.168.1.190         62
LAN_C      192.168.1.192/27   255.255.255.224 192.168.1.193 - 192.168.1.222         30
WAN1       192.168.1.224/30   255.255.255.252 192.168.1.225 - 192.168.1.226          2
WAN2       192.168.1.228/30   255.255.255.252 192.168.1.229 - 192.168.1.230          2

$ netkit summarize 172.16.0.0/24 172.16.1.0/24 172.16.2.0/24 172.16.3.0/24
172.16.0.0/22
```

## Library

```python
from netkit import RoutingTable, link_state_tables

rt = (RoutingTable()
      .add("0.0.0.0/0", "ISP")
      .add("10.0.0.0/8", "R1")
      .add("10.1.0.0/16", "R2"))
rt.lookup("10.1.4.20")        # 'R2': the most specific route wins

topology = {
    "A": {"B": 7, "C": 9, "F": 14},
    "B": {"A": 7, "C": 10, "D": 15},
    "C": {"A": 9, "B": 10, "D": 11, "F": 2},
    "D": {"B": 15, "C": 11, "E": 6},
    "E": {"D": 6, "F": 9},
    "F": {"A": 14, "C": 2, "E": 9},
}
link_state_tables(topology)["A"]["E"]   # ('C', 20): forward to C, total cost 20
```

## Testing

```bash
pytest
```

Besides hand-checked textbook cases, 300 random networks are compared with the standard library for network address, broadcast address and host count.

## Roadmap

- IPv6 addressing (EUI-64, prefix delegation)
- Distance-vector routing (Bellman-Ford) with split horizon, to contrast with link-state
- Export of an addressing plan to CSV and Markdown

## License

MIT. See [LICENSE](LICENSE).
