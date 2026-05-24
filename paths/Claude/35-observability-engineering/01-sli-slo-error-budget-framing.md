# SLI • SLO • error budget — observability framing

## Phase framing — Observability Engineering (`35`)

**Units in this folder:** `01`–`06` (topic order).

### Why a dedicated phase exists

Incident workflow without **measurable reliability contracts** degenerates into heroics. Staff-level expectation: you **own observability discipline** tied to **product risk**, not only dashboards.

### Core vocabulary (fluent, not ceremonial)

**SLI** — concrete ratio you trust (latency threshold, availability, error rate freshness).  

**SLO** — target + window for that SLI (what «good» means monthly / quarterly).  

**Error budget** — headroom remaining before SLO breach; governs velocity vs freeze decisions.  

**Alerting strategy** — every alert maps to owner, runbook snippet, severity, consumer (not «CPU high» orphaned pages).

### Golden Signals & families

Briefly reconcile **golden signals** (latency, traffic, errors, saturation) with **RED** (Rate, Errors, Duration) for request services and **USE** (Utilization, Saturation, Errors) for resources—but **adapt labels** to your stack (Symfony edge, Go workers, RabbitMQ depth, DB connections).

### Cross-links

Amplifies **`10-claude-ops-engineer`** (incidents) and **`06`** final-lab appendix—now first-class spine.

---

**Theme:** Reliability choices **written down** → SLI selects → dashboards prove → paging policy matches cognitive load budgets.
