# Unit 2 — Labs: cascading tabletop & degraded modes

Deliver **three** failure narratives (`Redis down`, **DB slow**, **queue backlog explosion**) using the reference stack (**Gateway → Symfony → Go worker → Postgres**).

Each narrative must specify:

```
user-visible symptom
metric / trace / log triage anchors
chosen degradation posture (checkout vs ancillary features)
recovery validation steps
preventive guard for next outage class
```

