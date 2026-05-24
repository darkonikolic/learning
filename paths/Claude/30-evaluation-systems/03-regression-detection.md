# Regression detection — baseline discipline

**Theme:** Winning yesterday guarantees nothing—**baseline snapshots** expose subtle decay.

Operational pattern:

```
 capture BASELINE artefacts (responses, diagrams, SPEC alignment notes)
                         → rerun IDENTICAL golden task later (e.g., +30 days horizon)
                                                                    → DIFF dimensions: correctness, tradeoff depth, security posture, maintainability signals
                                                                              → classify QUALITY DRIFT severity & hypothesise causal drivers (model, Rules, Retrieval noise)
                                                                                           → optimise or rollback platform configuration deliberately
```

**LAB rehearsal**

Symfony **refund flow** synthesis captured as **v1** packet—archive verbatim (git object or hashed bundle).

After deliberate waiting window (30 days illustrative), regenerate **v2** under controlled conditions.

Compare ruthlessly—not only prose similarity—structural fidelity to authoritative SPEC excerpts, enumerated tradeoffs, security cautions surfaced.

Discuss **baseline ownership**: who safeguards archive integrity & rotation policy.

Discuss **evaluation suite linkage**: regressions escalate changes to Retrieval indexes, SKILL drift, ephemeral temperature misuse—analytics not punishment theatre.

Small frequent micro-benchmarks complement heavy annual reruns capturing slow trend erosion early.

### Checklist

- [ ] Baselines store **prompt + frozen context snapshot ids** enabling faithful replay—not ambiguous memory.  
