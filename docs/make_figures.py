"""Regenerate the figures in docs/images from the library itself.

    pip install -e . matplotlib
    python docs/make_figures.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from netkit import IPv4Network, int_to_ip, vlsm

OUT = Path(__file__).resolve().parent / "images"
plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False})


def vlsm_map() -> None:
    base = IPv4Network.parse("192.168.10.0/24")
    needs = {"Labs": 100, "Admin": 50, "Library": 25, "Servers": 12, "WAN-1": 2, "WAN-2": 2}
    plan = vlsm(base, needs)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    colors = plt.cm.tab10.colors
    for i, (name, net) in enumerate(sorted(plan.items(), key=lambda kv: kv[1].network)):
        start = net.network - base.network
        ax.barh(0, net.size, left=start, color=colors[i], edgecolor="white")
        used = needs[name]
        ax.barh(0, used, left=start + 1, height=0.25, color="black", alpha=0.35)
        if net.size >= 16:
            ax.text(start + net.size / 2, 0, f"{name}\n/{net.prefix}", ha="center", va="center", fontsize=8, color="white")
            ax.text(start, -0.5, str(start), ha="center", fontsize=7)
        else:  # too narrow for an inside label: annotate above
            ax.annotate(f"{name}  .{start}/{net.prefix}", (start + net.size / 2, 0.42),
                        xytext=(start - 14 + 10 * (i % 2), 0.62 + 0.2 * (i % 2)), fontsize=8,
                        ha="right", arrowprops={"arrowstyle": "-", "lw": 0.6})
    ax.set(xlim=(0, 256), ylim=(-0.7, 1.0), yticks=[], xlabel="last octet of 192.168.10.0/24",
           title="VLSM plan, largest subnet first (dark band = hosts required)")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(OUT / "vlsm_plan.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    vlsm_map()
