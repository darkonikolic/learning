# Unit 7 — Delivery semantics: at-most-once, at-least-once, and “exactly-once” marketing vs engineering honesty

Distributed messaging rarely matches marketing slogans. Your job is to state what your system actually provides and what handlers must tolerate.

## Semantics sketch

**At-most-once**  
A message might never arrive. You must not rely on implicit delivery unless the business accepts loss.

**At-least-once**  
Duplicates are possible unless you dedupe/idempotently process. RabbitMQ workloads are commonly in this territory unless you add strict dedupe semantics elsewhere.

**“Exactly-once”**  
Often shorthand for engineered outcomes (idempotent handlers + dedupe keys + transactional outbox patterns), not an OS/network primitive you get for free.

## Practice

Replay the same queued job twice deliberately. Confirm your consumer does not corrupt state (`INSERT` blindly without keys, naive counters exploding, duplicate side effects).

## Interview prompts

- What does your broker actually guarantee vs what your application must guarantee?
- Where do you dedupe—in DB, metadata store, keyed business tables?
