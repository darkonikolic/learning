# Implementer + QA agents

**Theme:** Separation of creation vs independent verification lowers blind spot density.

Workflow cadence exercised:

```
 Architect frozen slice acknowledgement
           → IMPLEMENTER concrete changes (narrow diff discipline)
                         → QA validation pass (SPEC alignment + risk resurfacing)
                                        → iterative REPAIR loops governed by QA findings backlog
```

**Implementer stance:** Executes authorised plan—does **not** self-award production approvals / destructive infra applies—Ops retains those credentials in production-grade flows.

Practice drills:

Go **worker retry** policy nuanced adjustments—implementer honours architected idempotency story.  

Symfony **refund aggregate** behavioural patch implementing frozen invariants—not opportunistic refactors bleeding scope.

**QA stance:** hunts **SPEC drift**, latent **risk resurfacing**, **constraint violations**—including performance / security regressions tied to acceptance language.

Mandatory lab choreography: QA issues block closure until enumerated—Implementer forbidden from waving away without recorded disposition (fix / defer rationale / escalate Architect refresh).

Discuss failure mode: QA too shallow becomes cheerleading—stretch scenarios intentionally adversarial ethically.

### Checklist

- [ ] QA artefacts cite **checks executed** versus assumed—traceability defeats hand-wavy LGTM inertia.  
