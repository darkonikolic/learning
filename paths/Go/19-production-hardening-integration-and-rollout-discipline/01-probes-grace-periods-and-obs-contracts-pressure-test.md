# Unit 1 — Probes, grace periods & observability “contracts” (pressure-test mindset)

Reuse ideas from Area 17, but now treat them as **operational contracts** that can misbehave.

## Drill prompts (answer each in writing)

- When would **`/health` pass** while users see errors—and is that acceptable?
- How do misconfigured probes create **restart loops** vs **traffic black holes**?
- How does **`terminationGracePeriodSeconds`** relate to `Shutdown` timeouts in Go?
- What metrics/traces/logs would convince you **which** subsystem is saturated under load—not vibes?

Goal: articulate **signals you’d insist on before shipping** beyond “Dockerfile exists.”

