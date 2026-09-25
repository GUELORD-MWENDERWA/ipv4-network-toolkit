"""IPv4 addresses and networks.

Addresses are handled as 32-bit integers so every operation is a visible bit
manipulation: the network address is `ip & mask`, the broadcast is
`network | ~mask`, and so on.
"""

from __future__ import annotations

from dataclasses import dataclass

FULL = 0xFFFFFFFF


def ip_to_int(ip: str) -> int:
    parts = ip.strip().split(".")
    if len(parts) != 4:
        raise ValueError(f"invalid IPv4 address {ip!r}")
    value = 0
    for p in parts:
        if not p.isdigit() or not 0 <= int(p) <= 255 or (len(p) > 1 and p[0] == "0"):
            raise ValueError(f"invalid IPv4 address {ip!r}")
        value = (value << 8) | int(p)
    return value


def int_to_ip(value: int) -> str:
    return ".".join(str((value >> s) & 0xFF) for s in (24, 16, 8, 0))


def mask_from_prefix(prefix: int) -> int:
    if not 0 <= prefix <= 32:
        raise ValueError("prefix must be between 0 and 32")
    return (FULL << (32 - prefix)) & FULL


def prefix_from_mask(mask: str | int) -> int:
    m = ip_to_int(mask) if isinstance(mask, str) else mask
    prefix = bin(m).count("1")
    if mask_from_prefix(prefix) != m:
        raise ValueError(f"non-contiguous subnet mask {int_to_ip(m)}")
    return prefix


def address_class(ip: str) -> str:
    first = ip_to_int(ip) >> 24
    for bound, cls in ((127, "A"), (191, "B"), (223, "C"), (239, "D")):
        if first <= bound:
            return cls
    return "E"


@dataclass(frozen=True, order=True)
class IPv4Network:
    network: int
    prefix: int

    @classmethod
    def parse(cls, text: str, strict: bool = False) -> "IPv4Network":
        """Parse '192.168.1.0/24' or '192.168.1.0 255.255.255.0'.

        With strict=False, host bits are cleared ('10.1.2.3/8' -> 10.0.0.0/8).
        """
        text = text.strip()
        if "/" in text:
            addr, pfx = text.split("/")
            prefix = int(pfx)
        else:
            addr, mask = text.split()
            prefix = prefix_from_mask(mask)
        ip = ip_to_int(addr)
        net = ip & mask_from_prefix(prefix)
        if strict and net != ip:
            raise ValueError(f"{text} has host bits set")
        return cls(net, prefix)

    @property
    def mask(self) -> int:
        return mask_from_prefix(self.prefix)

    @property
    def wildcard(self) -> int:
        return ~self.mask & FULL

    @property
    def broadcast(self) -> int:
        return self.network | self.wildcard

    @property
    def size(self) -> int:
        return 1 << (32 - self.prefix)

    @property
    def usable_hosts(self) -> int:
        if self.prefix == 32:
            return 1
        if self.prefix == 31:
            return 2  # RFC 3021 point-to-point links
        return self.size - 2

    @property
    def first_host(self) -> int:
        return self.network if self.prefix >= 31 else self.network + 1

    @property
    def last_host(self) -> int:
        return self.broadcast if self.prefix >= 31 else self.broadcast - 1

    def __contains__(self, ip: str | int) -> bool:
        value = ip_to_int(ip) if isinstance(ip, str) else ip
        return value & self.mask == self.network

    def overlaps(self, other: "IPv4Network") -> bool:
        return self.network <= other.broadcast and other.network <= self.broadcast

    def is_private(self) -> bool:
        return any(self.network in n and self.broadcast in n for n in _PRIVATE)

    def __str__(self) -> str:
        return f"{int_to_ip(self.network)}/{self.prefix}"

    def describe(self) -> dict[str, str | int]:
        return {
            "network": str(self),
            "mask": int_to_ip(self.mask),
            "wildcard": int_to_ip(self.wildcard),
            "broadcast": int_to_ip(self.broadcast),
            "first_host": int_to_ip(self.first_host),
            "last_host": int_to_ip(self.last_host),
            "usable_hosts": self.usable_hosts,
            "class": address_class(int_to_ip(self.network)),
            "private": self.is_private(),
        }


_PRIVATE = [IPv4Network.parse(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
