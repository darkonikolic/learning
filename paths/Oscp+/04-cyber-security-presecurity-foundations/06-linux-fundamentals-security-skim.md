# Unit 06 — Linux fundamentals skim (security angle)

## Theme

Harvest parallel reinforcement—don't relive beginner grind fully.

**Constraint:** assuming Phase one Linux completeness **honestly**, skim TryHackMe **Linux Fundamentals** arcs where they appear — prioritize deltas & security glimpses—not re-solving trivial tasks unless memory gaps surface.

Ubuntu micro refresh:

```bash
ps aux | head
top -b -n1 | head
journalctl --since "30 min ago" | tail -n 40 || true  # shorten window if noisy
chmod --help >/dev/null
ssh -V 2>/dev/null || true
curl -I https://example.com
```

## Learning outcome

You consolidate identity of processes, persistence-location classes, and mutable configuration surfaces from a security lens—not another generic shell tutorial pass.
