# Deadlock ownership

**Theme:** Concurrent enterprise flows hit **ordering inversions** inevitably—architecture-grade DB practice names resources, timelines, mitigation — not mystical “bad luck”.

### Mechanical narrative

Circular wait graphs across **rows / gaps / auxiliary locks** surfaced by engine deadlock monitors.

### OWNERSHIP artefacts

Declare **consistent resource acquisition order** (table / account id monotone locks) wherever feasible.  

Tune **timeouts + bounded retries** distinguishing transient deadlock vs poisonous logic loops.  

Log **minimal victim excerpt** responsibly (identifiers not secret payloads).

### LAB — deliberate deadlock theatre

Twin domains:

**Payment strand** reserving ledger rows conflicting with ancillary balance adjustments.  

**Inventory strand** row locks acquired opposite sequence across two workers.

Produce reproducible deadlock graph exposition + explain **chosen victim rationale** surfaced by engine.

### Checklist

- [ ] Post-fix validation proves reduced **false retry storms** harming latency SLO—not only fewer deadlocks on paper while amplifying starvation.  
