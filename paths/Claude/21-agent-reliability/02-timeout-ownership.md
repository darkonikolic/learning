# Timeout ownership

**Theme:** Unguarded waits are silent **outage multipliers**—every hop gets a **deadline** with an explained rationale.

Failures to avoid:

Agent or tool waits **without bound**, stalling downstream personas and draining operator patience. Implicit “eventually” contracts when dependencies are flaky.

### Ownership questions (answer per workflow slice)

Which operations are **latency-sensitive** vs **correctness-sensitive**?

What is the **budget** per step (Planner ideation burst, MCP round-trip, relational query slice)?  

On timeout: **retry**, **fallback**, **abort slice**, or **escalate**—pick deliberately.

### Practice angles

Planner step with **generation ceiling** — stop rewriting plans indefinitely.  

Ops / automation **tool timeout** vs hanging cluster API.  

**DB query timeout** guarding analyst-style scans masquerading as OLTP helpers.

LAB: enumerate **minimum two distinct timeout scenarios** per end-to-end workflow rehearsal—for different layers (human-scale pacing vs subsystem call budgets).

Articulate **why** each limit exists—tie to blast radius / cost / user-visible SLO—not arbitrary round numbers devoid of reasoning.

Discuss interaction with retries: timeouts times retry budget must remain **bounded globally** (`max_attempts × per_attempt_deadline ≤` sensible wall clock).

### Checklist

- [ ] Timeouts surfaced in artefact summaries—not only buried in infra config unnoticed by orchestration reviewer.  
