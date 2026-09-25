"""Subnetting, VLSM allocation and route summarisation."""

from __future__ import annotations

import math

from .ipv4 import IPv4Network


def split(net: IPv4Network, new_prefix: int | None = None, count: int | None = None) -> list[IPv4Network]:
    """Split a network into equal subnets, by target prefix or by minimum number of subnets."""
    if (new_prefix is None) == (count is None):
        raise ValueError("give exactly one of new_prefix or count")
    if count is not None:
        new_prefix = net.prefix + math.ceil(math.log2(count)) if count > 1 else net.prefix
    if not net.prefix <= new_prefix <= 32:
        raise ValueError("new prefix must be longer than the original")
    step = 1 << (32 - new_prefix)
    return [IPv4Network(net.network + i * step, new_prefix) for i in range(1 << (new_prefix - net.prefix))]


def prefix_for_hosts(hosts: int) -> int:
    """Longest prefix whose subnet holds `hosts` usable addresses (network and broadcast excluded)."""
    if hosts <= 0:
        raise ValueError("hosts must be positive")
    return 32 - math.ceil(math.log2(hosts + 2))


def vlsm(net: IPv4Network, requirements: dict[str, int]) -> dict[str, IPv4Network]:
    """Variable-length subnet allocation.

    Subnets are allocated largest first, each aligned on its own size, which is
    the standard method and guarantees no overlap.
    """
    cursor = net.network
    result: dict[str, IPv4Network] = {}
    for name, hosts in sorted(requirements.items(), key=lambda kv: (-kv[1], kv[0])):
        prefix = prefix_for_hosts(hosts)
        size = 1 << (32 - prefix)
        cursor = (cursor + size - 1) // size * size  # align
        sub = IPv4Network(cursor, prefix)
        if sub.broadcast > net.broadcast:
            raise ValueError(f"not enough address space for {name} ({hosts} hosts)")
        result[name] = sub
        cursor += size
    return result


def summarize(networks: list[IPv4Network]) -> IPv4Network:
    """Smallest single prefix covering every network (route aggregation / supernetting)."""
    if not networks:
        raise ValueError("no networks to summarise")
    low = min(n.network for n in networks)
    high = max(n.broadcast for n in networks)
    prefix = 32 - (low ^ high).bit_length()
    return IPv4Network(low & ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF), prefix)
