# Regression prevention

**Theme:** The principal failure mode of “optimisation” is **fixed A, broke B**. Every change rides with **paired regression vigilance.**

### Workflow internalised

```
 CHANGE lands (code, Claude retrieval mapping, Skill shape, infra knob)
           → MEASURE primary KPI deltas
                              → structured COMPARE versus pre-change baseline
                                                             → targeted REGRESSION probes on coupled surfaces
                                                                              → rollback or gated forward based on DECISION artefact honesty
```

### Illustrative coupling checks

Tune **retrieval chunking** for tokens → re-run grounding quality probes + **approval-sensitive** workflows still parse policies.

Adjust **Go retry** policy → inspect **queue depth**, **downstream DB pressure**, error budget—not only local latency.

Tweak **Symfony** caching boundary → verify **staleness** acceptance paths + integration tests around invalidated reads.

Terraform module “simplification” → run plan diff sanity + **rollback path** rehearsal where state sensitive.

### LAB invariant

Attach a **Regression check** subsection to **every optimisation experiment**—even if bullets read “verified unchanged: X/Y/Z”—avoid blank silence implying safety.

Discuss **automated guards**: flaky tests tightened opportunistically when touching related modules.

### Checklist

- [ ] Regression list names **worst plausible surprise** domains—not only happy-path smoke.  
