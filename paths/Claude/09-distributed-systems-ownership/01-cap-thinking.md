# CAP thinking — distributed framing

## Phase framing — Distributed Systems Ownership (“Phase 5.7”)

**Units in this folder:** `01`–`08` (topic order only).

### Themes you carry throughout

**CAP** • **consistency models** • **eventual consistency** • **outbox pattern** • **saga pattern** • **circuit breaker** • **bulkhead** • **rate limiting** • **failure propagation** • **idempotency ownership**

### Lifecycle spine

```
 Request  →  Queue  →  Service  →  Storage  →  Recovery
```

Treat each arrow as having **explicit ownership**: latency budgets, duplication class, rollback posture, observable proof.

### Mindset checkpoint

Comfort moves from modelling **HTTP + broker plumbing** loosely to asserting **distributed ownership**: what may diverge, for how long, who heals it, under which tests.

### Distributed slice worksheet (reuse per lab)

| Column | Holds |
|--------|-------|
| **Slice / flow** | E.g. “authorize capture”, “stock reservation”. |
| **Consistency class** | What readers may assume (monotonic?, bounded staleness?). |
| **Failure modes** | Duplicates, delay, reorder, partial commit, poison. |
| **Idempotency** | Stable keys / dedupe horizon / uniqueness strategy. |
| **Recovery** | Retries vs compensations vs human queue. |
| **Verification** | Metrics, traces, property-style scenarios. |

---

**Theme (this unit):** **CAP intuition** baked into architectural choices—not folklore.

### Letters (pragmatic grounding)

CAP is about tension under **partition** (lost/delayed messages, split brains, asymmetric visibility).

| Pole | Probe |
|------|-------|
| **Consistency** | Observational agreement about fresh writes **you care about**. |
| **Availability** | System continues yielding responses under degraded paths (sometimes degraded fidelity). |
| **Partition tolerance** | You **must** design for unreliable links or clock skew when systems split. |

Rarely literal “toggle two of three”: real systems articulate **narrow strong islands** surrounded by deliberate eventual seams.

### LAB — payment ownership CAP lens

Enumerate:

- Moments requiring **narrow transactional truth** vs tolerating **delayed projection**  

- **Partition** manifestations in your sketch (payments API vs PSP webhook vs ledger DB).  

Penalise hand-wavy “ACID solves it” spanning multiple runtimes/brokers.

### Checklist

- [ ] For each externally visible payment state, labelled **consistency tier** ties to SLA + consumer contract.  
