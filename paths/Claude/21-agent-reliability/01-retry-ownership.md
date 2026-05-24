# Retry ownership — reliability framing

## Phase framing — Agent Reliability (“Phase 8.7”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

One assistant mistake or tool glitch must not **freeze the workflow**. The system **detects**, optionally **falls back**, **repairs**, and **continues**—with explicit ownership of verification and confidence—not endless manual salvage every time.

Target stack arcs: Symfony, Go, relational data, Terraform, Kubernetes, deploys, incidents—failure is ordinary; **controlled recovery** is the skill.

### Theme map

**Retry**, **timeouts**, **fallback**, **hallucination recovery**, **verification ownership**, **confidence ownership**, **repair loops**, **graceful degradation**, **agent health**, **escalation ownership**

Treat **agent health** operationally: repeated failures, stagnant repair loops, or chronic low **confidence** are signals to reroute work (narrow scope, alternate checks, human takeover)—not indefinite retries.

### Claude Reliability Template — substantive workflows

| Field | Holds |
|-------|-------|
| **FAILURE** | Symptom class (transient infra, logical error, stale context, tool error). |
| **DETECTION** | Signals that prove failure (tests, asserts, checksums, contract violations). |
| **CONFIDENCE** | Score or rubric—is output grounded enough to trust before acting? |
| **VERIFY** | Independent checks vs sources of truth—not “model said OK.” |
| **RETRY** | Budget, backoff, jitter, idempotency preconditions—what counts as safe retry. |
| **TIMEOUT** | Limits per phase (Planner, tool, DB query)—and what happens when hit. |
| **FALLBACK** | Degraded path while partial failure persists (cached read, manual ticket, narrower scope). |
| **ESCALATION** | When autonomy stops—human reviewer, Ops approval, incident bridge. |
| **REPAIR** | Concrete edit or state fix after verification failure—then re-verify. |

**Checkpoint mantra:** the story shifts from **“AI run succeeded”** to **“AI workflow survives failures.”**

This layers on orchestration + shared state—you still honour contracts, checkpoints, approvals.

---

**Theme (this unit): Retry ownership**

Retry is not “spam the button.” It is **bounded, idempotent-aware recovery**:

| Anti-pattern | Discipline |
|--------------|-------------|
| Infinite retry masking poison messages | Hard cap **N**, then classify / dead-letter |
| Immediate tight loops | **Backoff** + **jitter** to protect dependencies |
| Retry without escalation path | After budget: **human** or **alternate strategy** |

**Practice sketches**

Go **worker timeouts** — separate transport retries from domain retries.  

Symfony **payment** transient PSP failures vs hard declines—different retry eligibility.  

**Terraform** transient API blips vs plan/apply logic errors—never conflate blindly.

### LAB invariant

Per retry policy you define, spell out explicitly: **how many attempts**, **max wall-clock span**, **what happens next** (escalate, fallback, stop).

### Checklist

- [ ] Retries declare **idempotency keys** or equivalent wherever duplicate side effects matter.  
