# Unit 04 — DNS, DHCP, NAT, ARP

## Theme

How systems locate peers and negotiate addresses on LAN/WAN borders.

## Study alignment

| Source | Focus |
|--------|-------|
| Practical Networking | DNS, DHCP, NAT, ARP |
| Selected CCNA | DNS operational basics, DHCP, NAT classifications conceptually |

## Ubuntu drills

Resolver checks:

```bash
dig google.com +short
nslookup google.com
host google.com
ip neigh show
```

## Wireshark drills

Capture **DNS** lookups during a benign browse session (`dns` display filter vocabulary). Correlate Question/Answer with what `dig` returned.

## Checklist vocabulary

FQDN/resolver recursion vs stub, TTL on records, DHCP offer/ack sequence at high level (not vendor exam trivia), NAT inside→outside tuple rewriting intuition,ARP/NDP neighbour discovery purpose.

## Learning outcome

Given a symptom (“name resolves inconsistently”), you articulate whether to suspect resolver path, captive portal/DHCP starvation class issues, stale ARP, or NAT/port mapping quirks—then pick the next factual measurement.
