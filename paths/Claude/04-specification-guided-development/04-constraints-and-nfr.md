# Constraints + NFR

**Theme:** Without constraints + measurable **non-functional** truths, Claude drifts toward generic CRUD.

## Functional guarantees (subset examples)

Enumerate behaviour-level constraints you mean:

- Retry semantics, cancel windows, refunds, entitlement rules …

## NFR catalogue (iterate per system)

Concrete numbers beat vibes:

| Class | Examples |
|-------|----------|
| Load | Peak **RPS** (e.g. 500 sustained vs burst) |
| Availability | Tier target (e.g. **99.95%**) and how measured |
| Latency | p50 / p95 / p99 thresholds that matter monetarily |
| Audit | immutable log, correlation IDs, retention |
| Security posture | Secrets handling baseline, GDPR touchpoints if any |

Adjust false precision — cite “target / hypothesis / TBD instrumentation” honestly.

## Practice

| Track | Focus |
|-------|--------|
| **Go** | **Payment API** — explicit quotas + timeout floors. |
| **Ops / Terraform** | **Deploy SPEC** blast radius per module; rollback SLA. |

## Lab

Attach an **NFR block** before implementation on every sizeable task retroactively add if missing).

## Checklist

- [ ] At least **one measurable** NFR or explicit “defer / unknown” rationale.  
- [ ] Constraints say **cannot** vs **prefer** clearly.  
