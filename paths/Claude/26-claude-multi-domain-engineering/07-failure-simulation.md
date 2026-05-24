# Failure simulation

**Theme:** Real systems fail—practice **controlled chaos** across AI and runtime tiers so repairs become muscle memory—not panic.

### Failure catalogue seeds (sandbox / disposable)

Broken or biased **retrieval** index excerpts  

Poisoned **memory / summary** state  

Worker **queue** saturation or stalled consumer   

**Terraform** partial apply divergence  

Relational **DB** locking / slow path  

**Agent routing** error—wrong persona leading  

Rollback rehearsal after deploy anomaly  

**Approval** skipped or forged in simulation—observe detection pathways

Expect orchestrated response:

DETECT anomalies with observability artefacts  

BOUNDED repair — state + code + policy updates  

CONTINUE under restored invariants + post-review

### LAB deliverable

Author `FAILURE_CATALOG.md` (illustrative) listing scenario, blast class, expected detector, owner, last drill date.

Cross-link **Principal Template**: each entry maps **FAILURE** + **OBSERVABILITY** hooks.

### Checklist

- [ ] Simulations never use **production secrets**—use fakes and isolated envs.  
