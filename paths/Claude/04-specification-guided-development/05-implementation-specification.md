# Implementation specification

**Theme:** Immediately before coding: an **operations-level spec** naming technologies and numeric knobs — still specification, **not yet** the codebase.

## Bad vs good

**Weak:** “Create a queue.”  

**Stronger example knob block:

- Broker: **RabbitMQ** (or substitute)  
- **Retry**: max **3**, exponential policy detail  
- **DLQ**: attach policy + poisoning handling  
- **Timeouts**: inbound HTTP, ACK budget, outbound calls  
- **Worker concurrency**: baseline **5** (hypothesis)  

## Practice

| Track | Focus |
|-------|--------|
| **Go** | **Distributed worker** fleet behaviour. |
| **Symfony** | **CQRS flow** sequencing + async hand-off spec. |

## Lab policy

Hard rule for training runs: Claude **does not emit production code blocks** until an **implementation spec** subsection exists naming stack + limits + rollout guard rails.

Implementation spec is glue between architecture narrative and keystrokes — keep it reversible if wrong.

## Checklist

- [ ] Retry / DLQ / idempotency / timeout story has **explicit numbers**.  
- [ ] MySQL specifics (indexes, partitioning hints) deferred here only if SPEC says “schema phase gate”.  
