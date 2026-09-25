import ipaddress
import random

import pytest

from netkit import (
    IPv4Network, RoutingTable, address_class, dijkstra, int_to_ip, ip_to_int,
    link_state_tables, prefix_from_mask, split, summarize, vlsm,
)


def test_conversions():
    assert ip_to_int("192.168.1.1") == 3232235777
    assert int_to_ip(3232235777) == "192.168.1.1"
    assert prefix_from_mask("255.255.255.192") == 26
    with pytest.raises(ValueError):
        prefix_from_mask("255.0.255.0")
    for bad in ("256.1.1.1", "1.2.3", "01.2.3.4", "a.b.c.d"):
        with pytest.raises(ValueError):
            ip_to_int(bad)


def test_network_properties_match_stdlib():
    rng = random.Random(1)
    for _ in range(300):
        prefix = rng.randint(0, 30)
        ip = int_to_ip(rng.getrandbits(32))
        mine = IPv4Network.parse(f"{ip}/{prefix}")
        ref = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
        assert str(mine) == str(ref)
        assert int_to_ip(mine.broadcast) == str(ref.broadcast_address)
        assert mine.usable_hosts == ref.num_addresses - 2


def test_info_and_classes():
    d = IPv4Network.parse("192.168.10.77/26").describe()
    assert d["network"] == "192.168.10.64/26"
    assert d["broadcast"] == "192.168.10.127"
    assert d["first_host"] == "192.168.10.65" and d["last_host"] == "192.168.10.126"
    assert d["usable_hosts"] == 62 and d["private"] is True
    assert address_class("10.0.0.1") == "A" and address_class("172.16.0.1") == "B"
    assert address_class("224.0.0.5") == "D"
    assert IPv4Network.parse("10.0.0.0/31").usable_hosts == 2


def test_split():
    subs = split(IPv4Network.parse("10.0.0.0/24"), count=6)
    assert len(subs) == 8 and all(s.prefix == 27 for s in subs)
    assert str(subs[-1]) == "10.0.0.224/27"


def test_vlsm_allocation_is_aligned_and_disjoint():
    alloc = vlsm(IPv4Network.parse("192.168.1.0/24"), {"A": 100, "B": 50, "C": 20, "W1": 2, "W2": 2})
    assert str(alloc["A"]) == "192.168.1.0/25"
    assert str(alloc["B"]) == "192.168.1.128/26"
    assert str(alloc["C"]) == "192.168.1.192/27"
    assert str(alloc["W1"]) == "192.168.1.224/30"
    nets = list(alloc.values())
    assert not any(a.overlaps(b) for i, a in enumerate(nets) for b in nets[i + 1:])
    with pytest.raises(ValueError):
        vlsm(IPv4Network.parse("192.168.1.0/24"), {"big": 300})


def test_summarize():
    nets = [IPv4Network.parse(f"172.16.{i}.0/24") for i in range(4)]
    assert str(summarize(nets)) == "172.16.0.0/22"
    assert str(summarize([IPv4Network.parse("10.1.1.0/24"), IPv4Network.parse("10.1.2.0/24")])) == "10.1.0.0/22"


def test_longest_prefix_match():
    rt = RoutingTable().add("0.0.0.0/0", "ISP").add("10.0.0.0/8", "R1").add("10.1.0.0/16", "R2").add("10.1.2.0/24", "R3")
    assert rt.lookup("10.1.2.3") == "R3"
    assert rt.lookup("10.1.9.9") == "R2"
    assert rt.lookup("10.9.9.9") == "R1"
    assert rt.lookup("8.8.8.8") == "ISP"


GRAPH = {
    "A": {"B": 7, "C": 9, "F": 14},
    "B": {"A": 7, "C": 10, "D": 15},
    "C": {"A": 9, "B": 10, "D": 11, "F": 2},
    "D": {"B": 15, "C": 11, "E": 6},
    "E": {"D": 6, "F": 9},
    "F": {"A": 14, "C": 2, "E": 9},
}


def test_dijkstra_and_link_state():
    dist, _ = dijkstra(GRAPH, "A")
    assert dist == {"A": 0, "B": 7, "C": 9, "D": 20, "E": 20, "F": 11}
    tables = link_state_tables(GRAPH)
    assert tables["A"]["E"] == ("C", 20)
    assert tables["E"]["A"][1] == 20
