# Unit 1 — Scope: failure engineering — operationalise probabilistic breakage

Mindset shift: classify AI-assisted mishaps systematically **before blame** → repair pipeline.

## Learning outcomes

- Failure archetypes aligning with foundational taxonomy plus:
  - **Ambiguity collapse**
  - **Specification contradiction**
  - **Constraint violation**
  - **Context starvation**
  - **Hallucinated dependency**
  - **Implementation drift**
  - **Ownership drift**
  - **Token / window pressure artefacts**
  - **Retry amplification loops**
  - **Tool / dependency outages**
- **Recovery ownership**: restore known-good state baseline.
- **Classification rubric**: triage urgency + blast radius quickly.
- **Repair workflow canonical steps**: STOP → Snapshot evidence → Isolate minimal repro → Decide human vs autonomous attempt → Instrument → Retry bounded → Escalate.
- **Escalation workflow**: triggers (security ambiguous, systemic perf regression, unresolved contradiction).
- **Post-repair enrichment**: tighten rule / prompt capsule / SKILL / checklist.

Feeds orchestration narratives **`13-*`**, tooling degradation **`14-*`**.
