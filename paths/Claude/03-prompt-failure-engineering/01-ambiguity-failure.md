# Ambiguity failure

## Phase framing (Prompt Failure Engineering)

Topics **`01`–`05`**.

**Mindset:** bad output → classify **failure class** → repair prompt/context/spec — not only patch prose by hand.

| Class | Meaning |
|-------|---------|
| **Ambiguity** | Underspecified wording; model guesses stack. |
| **Missing context** | Not enough system truth. |
| **Constraint failure** | Forbidden/allowed tech not stated. |
| **Spec drift** | Answer leaves your locked SPEC. |
| **Token / over-context** | Too much noisy paste. |
| **Role failure** | Wrong reviewer stance. |
| **Verification failure** | You skipped SPEC/criteria check. |

**Daily drill (recommended):** 1× Symfony + 1× Go + 1× Ops — each with an **intentionally bad prompt** → diagnose → repaired prompt → re-run → one-line lesson.

**Checkpoint:** Stop at “wrong”; start at **“I know why it failed.”**

---

**Theme:** The most common failure — you said a **word**, not a **decision surface**.

## Pattern

**Weak:** “Build a worker.”  
The model must guess: **RabbitMQ consumer? cron? goroutine pool? cloud task?** — each is a different architecture.

**Diagnosis label:** **ambiguity** (noun/verb not tied to your system).

## Practice — tighten the same ask

### PHP / Symfony

| Weak | Stronger |
|------|----------|
| “Build an order flow.” | Name **DDD** boundaries, **CQRS** split, **payment retry** rules, **refund ownership** — who may initiate what. |

### Go

| Weak | Stronger |
|------|----------|
| “Build a queue.” | Name **RabbitMQ** (or your broker), **retry**, **DLQ**, **worker pool** sizing assumptions, idempotency expectations. |

## Lab — daily drill (short)

Write **five intentionally vague prompts** (mix stacks). For each, **classify** the likely failure as **ambiguity** (or note if another class also applies). Then rewrite **one** into a non-ambiguous prompt (add CONTEXT + CONSTRAINT + SPEC).

**Measure:** count how many guesses disappear in the first reply.

## Checklist

- [ ] Every actor noun has a **single** interpretation in your org (worker = what exactly?).  
- [ ] Verbs like “optimize” / “build” are replaced by **observable outcomes**.  
