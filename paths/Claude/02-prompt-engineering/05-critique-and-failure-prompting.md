# Critique + failure prompting

**Theme:** Use the model to **attack** its own draft before you treat it as a plan.

## Workflow

```
generate → critique → surface risks → repair / rewrite
```

## Practice rotations

| Track | Exercise |
|-------|----------|
| **PHP / Symfony** | **CQRS refactor** — command/query split, event boundaries. |
| **Go** | **Distributed retry** — double delivery, idempotency, poison messages. |
| **Ops** | **Incident rollback** — what to revert, what to keep, comms shape. |

## Lab — three-pass minimum

1. **Implement / plan** (first answer).  
2. **Critique your previous answer** under a reviewer ROLE (security, staff engineer, SRE — pick one).  
3. **Produce improved v2** that lists what changed and why.

**Measure:** count of **caught risks** in step 2 that step 3 actually fixes.

## Failure prompting (explicit)

Add CONSTRAINTS like:

- “Assume partial outage of dependency D.”  
- “Assume duplicate message delivery.”  
- “Assume deploy during incident.”  

Then require **failure modes + mitigations**, not happy path only.

## Checklist

- [ ] Critique pass uses a **different ROLE** than generation.  
- [ ] You ask for **diff-style** “what failed in v1” before v2.  
