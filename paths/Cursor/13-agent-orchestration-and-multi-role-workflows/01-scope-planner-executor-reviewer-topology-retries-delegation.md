# Unit 1 — Scope: agent orchestration engineering — choreography with accountability

Mindset shift: multiple semi-autonomous steps require **topology + state machine thinking** — planners, executors, reviewers need explicit delegation contracts.

## Learning outcomes

- **Planner pattern**: decomposition referencing existing architecture map (`09-*`).
- **Executor pattern**: bounded autonomy windows + tool constraints.
- **Reviewer / adversarial role**: rejects patch lacking evidence or violating constraints (`07-*`).
- **Multi-agent coordination cautions**: hidden consensus illusions unless externalised diff reviews happen.
- **Delegation ownership clarity**: RACI overlays on autonomy segments.
- **Approval ownership**: enumerated gate transitions.
- **Capability routing**: model vs tool vs human specialist selection heuristics.
- **Retry ownership**: backoff + stop conditions — avoid doom loops (**`08-*`** echo).
- **Fallback ownership**: degrade plan when tool partial failure (**`14-*`** preview).
- **Escalation ownership**: stuck detection triggers.
- **Workflow ownership artefacts**: ephemeral plan docs / decision logs versioning.
- **Orchestration anti-patterns**: “telephone game summarisation loses truth”.
- **Agent topology sketches**: sequential vs DAG vs parallel guarded merge.
- **State ownership**: what lives in ephemeral chat vs persisted branch vs ticket.

Cross-link governance **`06-*`**, tools **`14-*`**, failures **`08-*`**.
