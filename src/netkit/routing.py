"""Forwarding by longest-prefix match, and link-state (OSPF-like) route computation."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from .ipv4 import IPv4Network, ip_to_int


@dataclass
class RoutingTable:
    routes: list[tuple[IPv4Network, str]] = field(default_factory=list)

    def add(self, prefix: str, next_hop: str) -> "RoutingTable":
        self.routes.append((IPv4Network.parse(prefix), next_hop))
        return self

    def lookup(self, ip: str) -> str | None:
        """Next hop of the most specific matching route, or None."""
        addr = ip_to_int(ip)
        best: tuple[int, str] | None = None
        for net, hop in self.routes:
            if addr in net and (best is None or net.prefix > best[0]):
                best = (net.prefix, hop)
        return best[1] if best else None


Graph = dict[str, dict[str, float]]


def dijkstra(graph: Graph, source: str) -> tuple[dict[str, float], dict[str, str | None]]:
    """Shortest path costs and predecessors from source. Link costs must be non-negative."""
    if source not in graph:
        raise KeyError(source)
    dist = {n: float("inf") for n in graph}
    prev: dict[str, str | None] = {n: None for n in graph}
    dist[source] = 0.0
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u].items():
            if w < 0:
                raise ValueError("negative link cost")
            nd = d + w
            if nd < dist[v] or (nd == dist[v] and prev[v] is not None and u < prev[v]):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    return dist, prev


def link_state_tables(graph: Graph) -> dict[str, dict[str, tuple[str, float]]]:
    """For every router, map each destination to (first hop, total cost), as OSPF would compute."""
    tables = {}
    for src in graph:
        dist, prev = dijkstra(graph, src)
        table = {}
        for dst in graph:
            if dst == src or dist[dst] == float("inf"):
                continue
            hop = dst
            while prev[hop] != src:
                hop = prev[hop]
            table[dst] = (hop, dist[dst])
        tables[src] = table
    return tables
