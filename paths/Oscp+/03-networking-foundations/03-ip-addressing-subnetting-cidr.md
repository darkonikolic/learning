# Unit 03 — IP addressing, subnetting, CIDR

## Theme

How hosts are numbered and partitioned.

## Study alignment

| Source | Sections |
|--------|----------|
| Practical Networking | IP Addressing, CIDR, Subnetting |
| CCNA fundamentals (selected) | Subnetting, CIDR deep enough to reason |
| Subnetting practice | [https://subnettingpractice.com/](https://subnettingpractice.com/) — maintain short daily sets |

## Ubuntu drills

```bash
ip a
ip route
ip -6 addr show
```

Interpret **addresses versus prefixes**.

## Drill problems (paper or scratch buffer)

Understand and annotate:

| Example | Annotate |
|---------|----------|
| `192.168.1.0/24` | network, broadcast, usable host ranges, gateway intuition |
| `10.0.0.0/8` | classless meaning today |
| `172.16.0.0/16` | private RFC1918 rationale |

Explain in your own words: **network address**, **host**, **broadcast**, **meaning of `/24`**.

## Topics

Private vs public IPv4 framing, baseline IPv6 awareness (dual-stack reality), gateway choice, overlapping/overlong prefixes as a conceptual misconfiguration trap.

## Learning outcome

You can answer “how many usable hosts?” and justify a carve without calculator dependency by the end of the unit—not necessarily instant mental math flawless, but structurally competent.
