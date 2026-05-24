# Specification drift

**Theme:** The model (or you) loses the thread — **implementation** diverges from the **SPEC** you intended to lock.

## Pattern

**SPEC said:** retry **max 3**.  
**Answer implements:** “retry until success” / unbounded loop.  

**Diagnosis label:** **spec drift** (answer no longer satisfies the stated acceptance criteria).

## Why it happens

- SPEC buried inside long prose.  
- Follow-up messages introduce new goals without restating SPEC.  
- No explicit “diff against SPEC” step in OUTPUT FORMAT.

## Practice rotations

| Track | Exercise |
|-------|----------|
| **Go** | **Payment retry** — numeric cap, idempotency key, DLQ behavior: write SPEC bullets first. |
| **PHP / Symfony** | **CQRS aggregate** change — invariants and command outcomes as checkable bullets. |

## Lab — force verification

1. Ask for **implementation / plan**.  
2. **Without new features in the prompt**, ask for a **SPEC compliance table**: each SPEC line → satisfied / violated / unclear → evidence quote from the answer.  
3. Mark **drift** rows and rewrite prompt or add CONSTRAINT / OUTPUT FORMAT requiring the table **in the first pass** next time.

## Checklist

- [ ] SPEC lives in **short bullets** that survive copy-paste into follow-ups.  
- [ ] OUTPUT FORMAT demands **traceability** back to SPEC when risk is high.  
