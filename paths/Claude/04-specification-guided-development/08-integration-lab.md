# Integration lab (Phase 3)

**Theme:** **Payment Platform** umbrella — Claude leads you through SPEC spine end-to-end, you keep **ownership of validation**.

## Required chain

```
Problem  
  → SPEC (fill every heading from the Unified SPEC template — Problem through Implementation spec gate)
  → Acceptance  
  → Architecture notes where needed  
  → Implementation Strategy + Tradeoff + Risk  
  → Implementation spec (numbered tech knobs — still pre-code gate)  
  → Implementation artefacts (only after SPEC gate)  
  → Validation proof (diff vs Acceptance bullets + flagged NFRs)
```

**Claude may draft** intermediate docs — **you** decide merge worthiness vs drift.

### Measure deliberately

| Metric | Notes |
|--------|--------|
| Iterations | Rework loops before acceptable SPEC |
| Quality | Peer sign-off heuristic |
| Spec drift incidents | Number of detected mismatches after implementation snapshots |

Avoid premature coding windows — reopen SPEC when mismatch count spikes.

### Stack rotation within lab

Sweep **Symfony + Go + Terraform + MySQL** surfaces so each SPEC partition faces reality constraints at least once per full exercise cycle when possible.

### Phase checkpoint restated

Operational phrase to internalize:

> **Stop:** Claude wrote code spontaneously.  

> **Start:** Claude instantiated / refined / aligned implementation to validated specification.
