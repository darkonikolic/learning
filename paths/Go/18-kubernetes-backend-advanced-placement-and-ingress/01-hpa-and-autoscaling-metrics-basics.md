# Unit 1 — Horizontal Pod Autoscaling (HPA) — backend mental model

Backend engineers should know **why** a Deployment might scale replicas without treating it as witchcraft.

Understand at a high level:

```
HPA reads metrics (often CPU/memory via metrics-server; custom metrics possible conceptually)
 adjusts desired replica count within min/max bounds subject to scheduling constraints
```

## Practice (paper / local cluster optional)

Sketch an API service with variable RPS: decide which metric you would scale on (CPU alone is often a weak proxy for IO-bound services—articulate limitations).

## Interview prompts

Why CPU autoscaling can amplify latency issues if the bottleneck is external (DB saturation).
