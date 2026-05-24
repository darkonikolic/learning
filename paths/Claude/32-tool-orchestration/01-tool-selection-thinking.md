# Tool selection thinking — orchestration framing

## Phase framing — Tool Orchestration (“Phase 11.8”)

**Units in this folder:** `01`–`05` (topic order only).

### Themes

**MCP / tool routing** • **permission ownership** • **retry / fallback ownership** • **capability ownership**  

**Tool unavailable**, **partial failure**, **retry escalation**, **fallback chains**, **tool degradation**

### Mindset pivot

| Weak | Strong |
|------|--------|
| “Explain the Symfony bug narrative.” | “**Which capability** solves it—**in what order**—with **what risk** gates?” |

**Checkpoint mantra:** Claude **orchestrates tools**—it does not merely answer in prose while pretending tools do not exist.

### Illustrative orchestration spine (order varies by incident)

Ordering is **example wiring**—real routes adapt to evidence:

```
 DB / datastore truth checks  →  FILESYSTEM grounding  →  GIT history causality
           → BROWSER authoritative docs/changelogs  
                     → DEPLOY / runtime execution surfaces — only behind approval tiers
```

Map this to MCP servers or native IDE tools your stack exposes—keep **routing ownership** explicit: who may invoke which modality.

---

### Claude tool orchestration checklist — per substantive task

| Field | Holds |
|-------|-------|
| **TOOL PLAN** | Ordered steps naming capability (DB query, grep repo, git log…). |
| **CAPABILITY OWNERSHIP** | Why this tool—not “because it exists”. |
| **PERMISSION CLASS** Per hop | Safe / approval / forbidden for each tool touched. |
| **RETRY + FALLBACK** | Budget per failing hop; degraded path if submodule dead. |
| **PARTIAL FAILURE** | Hypothesis when only one modality fails—how to proceed safely. |
| **RISK** | Blast radius of mistaken command / wrong credential scope. |
| **VERIFICATION** | Independent proof the tool chain output matches reality before “fix merges”. |

Themes align with **routing ownership** and **capability ownership**.

---

**LAB invariant**

Produce **TOOL PLAN bullets before deep execution** — Symfony **refund** defect & Go **worker timeout** style tabletops habitual.

### Checklist

- [ ] High-energy terminal / deploy hops appear **after** evidence from read-mostly modalities unless emergency runbook dictates otherwise ethically.  
