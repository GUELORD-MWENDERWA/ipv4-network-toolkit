"""Command-line interface.

    netkit info 192.168.10.77/26
    netkit split 10.0.0.0/24 --count 6
    netkit vlsm 192.168.1.0/24 LAN_A=100 LAN_B=50 LAN_C=20 WAN1=2 WAN2=2
    netkit summarize 172.16.0.0/24 172.16.1.0/24 172.16.2.0/24 172.16.3.0/24
"""

from __future__ import annotations

import argparse

from .ipv4 import IPv4Network, int_to_ip
from .subnetting import split, summarize, vlsm


def _row(name: str, n: IPv4Network) -> str:
    hosts = f"{int_to_ip(n.first_host)} - {int_to_ip(n.last_host)}"
    return f"{name:10s} {str(n):18s} {int_to_ip(n.mask):15s} {hosts:33s} {n.usable_hosts:>6}"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="netkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info")
    p.add_argument("network")
    p = sub.add_parser("split")
    p.add_argument("network")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prefix", type=int)
    g.add_argument("--count", type=int)
    p = sub.add_parser("vlsm")
    p.add_argument("network")
    p.add_argument("needs", nargs="+", help="NAME=HOSTS")
    p = sub.add_parser("summarize")
    p.add_argument("networks", nargs="+")
    a = ap.parse_args(argv)

    header = f"{'name':10s} {'network':18s} {'mask':15s} {'host range':33s} {'hosts':>6}"
    if a.cmd == "info":
        for k, v in IPv4Network.parse(a.network).describe().items():
            print(f"{k:13s} {v}")
    elif a.cmd == "split":
        print(header)
        for i, n in enumerate(split(IPv4Network.parse(a.network), a.prefix, a.count)):
            print(_row(f"subnet{i}", n))
    elif a.cmd == "vlsm":
        needs = {k: int(v) for k, v in (x.split("=") for x in a.needs)}
        print(header)
        for name, n in vlsm(IPv4Network.parse(a.network), needs).items():
            print(_row(name, n))
    else:
        print(summarize([IPv4Network.parse(n) for n in a.networks]))


if __name__ == "__main__":
    main()
