# Unit 05 — Routing and packet path narratives

## Theme

How a datagram hops from laptop to internet service provider to remote server logically.

## Study alignment

| Source | Sections |
|--------|----------|
| Practical Networking | Routing, default gateway discourse |
| CCNA fundamentals (selected) | Routing introduction only |

## Ubuntu drills

```bash
ip route
traceroute google.com
tracepath google.com
```

Interpret **hop growth**—where latency spikes first.

## Narrative model (produce your sketch)

Produce a handwritten or diagrammable story:

```
Laptop → LAN router/NAT → ISP → Internet ↔ remote network → destination host
```

Label where **routing decision**, **NAT rewrite**, potential **VPN tunnel** would appear if VPN later overlays.

## Checklist vocabulary

Default route, longest-prefix match intuition, asymmetric routing caveat, TTL decrement as rough hop counter anecdote—not deep BGP policy.

## Learning outcome

When `ping` works but traceroute stalls at hop *k*, you can hypothesize plausible classes of causes and what extra evidence distinguishes them—not instant diagnosis perfection.
