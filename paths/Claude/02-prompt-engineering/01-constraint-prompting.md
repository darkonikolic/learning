# Constraint prompting

## Phase framing (this learning area)

Numbered topics **`01`–`07`** = topic order.

**Decomposition:** 3–7 steps in **your own words** before you prompt — same reflex as Phase 1 workflow-thinking. Poor decomposition ⇒ bloated CONTEXT.

| # | Focus |
|---|--------|
| 01 | Constraint prompting *(here)* |
| 02 | Role prompting |
| 03 | Architecture prompting |
| 04 | Debug prompting |
| 05 | Critique + failure prompting |
| 06 | Optimization prompting |
| 07 | Integration lab |

**Practice stacks:** PHP/Symfony (DDD+CQRS) • Go/`sqlx`/workers • Ops/incidents • Terraform-style IaC where relevant.

**Measure when useful:** quality (would a senior merge it?), approximate tokens or turns, time to usable draft.

| Stop saying | Start saying |
|-------------|---------------|
| “I know prompts” | “I know **workflows** for problem type **X**” |

**Checkpoint:** Shift from chasing one strong prompt alone to owning **pattern ⇄ problem-type** workflows (architecture / debug / ops / review / spec / refactor / incident).

---

**Theme:** Constraints are how you stop the model from inventing your org’s real boundaries.

## The usual failure mode

**Weak:** “Build a payment service.”  
**Strong:** Same ask, plus **explicit CONSTRAINTS** the answer must satisfy.

### Example constraint set (adjust to your truth)

- **Go** + **`sqlx`** (or your agreed DB layer)  
- **DDD** + **CQRS** boundaries you actually run  
- **Retry**, **timeout**, **idempotency** spelled as non-negotiables  
- **RabbitMQ** (or your broker) in the picture  
- **No ORM** if that is your rule  

## Practice rotations

| Track | Exercise idea |
|-------|----------------|
| **PHP / Symfony** | One **aggregate**-level change (rules, invariants, boundaries). |
| **Go** | End-to-end **payment flow** sketch: where idempotency lives, who owns retries. |
| **Ops** | One **Terraform module** (or slice): what it touches, rollback story, blast radius. |

## Lab — same problem, two passes

1. **Without** listing constraints (observe hallucinated stack / missing invariants).  
2. **With** the constraint block (observe fewer surprises, more reviewable output).

**Measure:** quality (1–5 or pass/fail checklist), **iteration count** to “good enough”.

## Checklist

- [ ] CONSTRAINTS are **testable** (yes/no), not vibes.  
- [ ] You stated **out of scope** explicitly.  
- [ ] You named **one decision** this session must unlock.  
