# Unit 2 — Labs & trade-offs: search ingestion, staleness, and failure containment

## Lab A — ingestion contract

Specify how documents/records enter the search index:

```
event-triggered incremental updates vs periodic bulk rebuild trade spectrum
ordering / duplicate resilience (tie to distributed ingestion patterns)
explicit schema/version field for rollback & reindex choreography
```

## Lab B — consistency narrative

Produce user-visible statement for **freshness SLA** (“search may lag writes by ≤ x minutes under normal churn”) tied to alerting if lag diverges dangerously.

## Review checklist

| Risk | Evidence you’d insist on |
|------|---------------------------|
| Hot queries overload cluster | latency metrics, shedding policy |
| Index skew / noisy neighbours | infra isolation story |
| PII leakage in index | field allow-lists |
| Divergent truth Postgres vs search | reconciliation job / breaker pattern |

