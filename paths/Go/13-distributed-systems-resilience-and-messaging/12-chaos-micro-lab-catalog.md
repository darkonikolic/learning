# Unit 12 — Chaos rehearsal catalogue (small, controlled fault injections)

Build intentional failure rehearsals—notebook/diagram-heavy is fine—to complement code:

| Fault | Symptoms you expect | Fix story you must articulate |
|-------|---------------------|-------------------------------|
| payment backend slow / flaky | timeout storms, cascading cancellation | tightened budgets + retry sanity + degraded UX policy |
| queue broker restart | backlog spike, duplicated deliveries surfaced | durable publisher confirms / consumer idempotency / DLQ path |
| worker crash mid-batch | orphaned partial writes unless transactional boundaries exist | transactional outbox glimpses responsibly optional advanced bridging |
| network partition caricature verbally | ambiguous success | idempotency + reconciliation queries patterns |

Produce a miniature **timeline write-up**: detection → containment → remediation → preventative guard next iteration.

Interview mindset: rehearsals beat heroics—you can describe how you practise partial failure calmly.
