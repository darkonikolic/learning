# Failure classification integration

**Theme:** On a **Payment platform** (or your single big scenario), you **inject** known-bad model behavior and practice **classify → repair → verify**.

## Bad output example (intentional stress test)

A plan that has, e.g.:

- **Unbounded retries**  
- **No timeouts**  
- **No idempotency** where money moves  

Your job is **not** to rage-edit the text — it is to **label** *why* the session produced this.

## Classification workflow

```
failure output  →  label (one or more classes)  →  repair plan  →  re-run  →  verify
```

### Labels to use (natural catalog by end of Phase 2.5)

| Class | Plain meaning |
|-------|----------------|
| **Ambiguity** | You never pinned what “worker”, “flow”, or “optimize” meant. |
| **Constraint failure** | Stack / style / bans were missing; wrong-idiom answer. |
| **Missing context** | Not enough system truth. |
| **Over-context / token pressure** | Too much or irrelevant paste; model fixates wrong. |
| **Spec drift** | Answer drifted from numeric / logical SPEC. |
| **Role failure** | Wrong reviewer mindset (e.g. no SRE when you needed blast-radius). |
| **Verification failure** | You never compared output to SPEC/constraints. |

## Repair plan template (short)

1. **Primary class** (and secondary if any).  
2. **Prompt change** — which block you add or tighten: CONTEXT, CONSTRAINT, SPEC, OUTPUT FORMAT, ROLE.  
3. **Verification** — one step that proves the next run can’t repeat the same drift without you seeing it.

## Lab — end checkpoint

Run one **deliberately weak** prompt → classify → repair → re-run. Log **one line**: *which class* bought the biggest quality jump.

## Phase 2.5 checkpoint

You move from **“Claude was wrong”** to **“The failure was X; the fix is Y.”**
