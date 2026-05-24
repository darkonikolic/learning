# Unit 02 — OSI, TCP/IP, TCP vs UDP, first captures

## Theme

How the internet delivers bytes end-to-end at a layered mental model level.

## Study alignment

| Source | Sections |
|--------|----------|
| Practical Networking | OSI Model, TCP/IP Model, TCP vs UDP |
| Selected CCNA fundamentals | Introduction, OSI, TCP/IP |
| Spot video | OSI / TCP–UDP recap if confused |

## Ubuntu drills

Run and interpret succinctly:

```bash
ping -c 4 google.com
tracepath google.com
curl https://example.com/
ss -tulpn | head -40
```

## Wireshark drills

Filters to practise (`tcp`), then revisit a browse session looking for **`SYN`, `SYN-ACK`, `ACK`** handshake segments on a benign site you authorize.

Ethics reminder: capture only labs you own authorization for.

## Checklist vocabulary

OSI layers (practical—not trivia regurgitation), TCP/IP shorthand, segmentation vs reliability, ICMP echo vs TCP, TTL intuition, fragmentation/MTU as a troubleshooting axis.

## Learning outcome

You can narrate handshake establishment and articulate what UDP forfeits versus TCP without hand-waving beyond your evidence.
