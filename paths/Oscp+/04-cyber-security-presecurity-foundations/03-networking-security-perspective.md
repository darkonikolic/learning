# Unit 03 — Networking through a security mindset

## Theme

Re-frame Phase two facts as **boundary & visibility** problems.

## TryHackMe — Network Fundamentals (PreSecurity-aligned segment)

Redo or validate modules around:

LAN vs broader segmentation intuition

OSI / packets vs frames mnemonic utility

Extend / route / boundary abstractions pedagogically surfaced there

Trust the authoritative module catalogue on-platform.

## Ubuntu refresh (short)

```bash
ping example.com -c 3
ip a
ip route
ss -tulpn | head -30
```

## Narrative exercise

Rebuild—without peeking—the chain:

browser → DNS → routing → TCP → server port binding

Identify **trust boundaries** attackers love (resolver lying class, rogue gateway class, interception—not detailed attacks yet).

## Learning outcome

You instinctively annotate attacker opportunities at each hop abstractly—even before exploiting.
