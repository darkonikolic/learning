# Unit 4 — Retry policies: backoff, jitter ceilings, disciplined caps

## Anti-pattern caricature

A naive “retry loop until success” hammering an already degraded dependency deepens outages: the caller looks “helpful” while it amplifies load and hides the real SLA breach.

## Responsible pattern skeleton

Implement a bounded retry helper (learning-scale is enough) with:

- a **maximum attempt count**,
- increasing delay between attempts (backoff shape you can justify),
- optional **jitter** to reduce thundering herds,
- clear classification: **retry only when duplication is safe or idempotent** (ties to Unit 5).

## Interview narration

Articulate **retry storms** as a second-order incident and why operators care about cooperative client behaviour—not only server health.
