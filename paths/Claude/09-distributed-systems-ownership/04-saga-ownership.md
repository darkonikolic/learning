# Saga ownership

**Theme:** **Distributed choreography** replaces a mythical global transaction; **you** own compensations, idempotency, and observability of long-running narratives.

Nominal choreography:

```
 payment intent accepted
      → inventory / fulfilment leg
           → notifications / ancillary writes
failure anywhere
      → deterministic compensation choreography (not silent hope)
```

### Failure → compensation realities

Define **backward actions** semantics: financial reversals rarely mirror forward steps atomically—inversion may be asynchronous, disputed, regulatory-gated—document honestly.

Prefer **explicit saga state**: pending / compensated / aborted + poison handling for stuck legs.

Contrast **choreography** (events only) vs **orchestration** (central conductor): choose knowingly; hybrids exist.

### Checklist

- [ ] Duplicate saga command delivery cannot double-charge inventory or treasury—proved via **idempotent** compensating logic.  
