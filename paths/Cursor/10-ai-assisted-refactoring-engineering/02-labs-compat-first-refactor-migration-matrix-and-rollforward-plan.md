# Unit 2 — Labs: phased refactor tabletop

Identify a refactor surface (duplicate error mapping, sprawling service class god object, transitional DTO bridging).

Produce:

### 1 — Invariants list (≥8 bullets)

Operational + behavioural + performance guard rails.

### 2 — Compatibility matrix table

Consumers | breakage risk | mitigation | deprecation window signal

### 3 — Automated safety net backlog

Existing tests augmented + gaps newly specified.

### 4 — Mechanical wave plan

Step ordering with **stop gates** (“after wave 2, deploy behind flag X” hypothetical ok).

### 5 — Abort criteria

Signals to halt assistant-driven sweeping edits immediately.

Conduct **dry rehearsal**: narrate rollback if Wave 3 introduces subtle race.

Deliverable: **`REFACTOR-PLAN.md`** suitable for attaching to RFC.
