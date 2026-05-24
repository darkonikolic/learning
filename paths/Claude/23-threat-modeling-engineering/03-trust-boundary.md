# Trust boundary

**Theme:** Security architecture is partly **explicit disbelief**: default-deny across boundaries beats implicit faith in homogeneous “internal nets.”

For each crossing, articulate:

WHAT crosses (commands, JWTs, events, migrations)  

WHO on each side (service identity vs human actor)

WHAT proofs exist (signatures, mTLS, IAM conditions, transactional constraints)

WHAT must **never** propagate unchanged (opaque trust of queue payload content from least-trusted tier)

LAB crossing sets you rehearse:

**Queue** ingestion edge (replay, poison, spoofed producers) versus consumers  

**External API ↔ App** tiers (JWT claims vs fine-grained authorisation downstream)  

**DB** session identity vs application-level row policies—who really enforces segregation  

**Workers** escalating DB privilege accidentally via shared pooled connections without scoping narratives

Discuss **privileged trust islands**: infra operators, break-glass creds—these merit extra logging & dual control even if ergonomically inconvenient.

Discuss **verification**: penetration assumptions invalidated when secret rotation or VPC layout shifts silently—boundary diagrams must evolve with infra PRs realistically.

Discuss **risk ownership residual**: acknowledging a boundary still partially trusted under business pressure—document compensating monitoring instead of silent hope.

### Checklist

- [ ] Trust boundaries appear on architecture diagrams **as lines with stated failure modes**—not decorative boxes only.  
