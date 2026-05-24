# Unit 5 — Idempotency: why payments + timeouts + retries are dangerous without keys

Classic failure story:

```
charge initiated → client times out unsure → retries → duplicate financial side-effect nightmares
```

## Learning outcomes

Treat **idempotency keys** (`request_id` / Stripe-style keyed requests, etc.—API-specific details belong in your docs, not folklore) as a design surface:

- deterministic dedupe keyed by caller intent scope,
- storage of accepted vs processed keys with explicit retention policy thinking,
- aligning HTTP status semantics with ambiguity (accepted vs succeeded).

## Practice

Simulate duplicated submit attempts verifying only one outward charge effect occurs under your deliberately imperfect timeout policy.

## Interview prompts

Distinction between *at-least-once delivery* honesty and pretending *exactly-once* globally.
