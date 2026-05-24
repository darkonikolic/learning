# Unit 7 — Lab: same payment intent initiation (Laravel twin)

Rebuild **Symfony lab slice** equivalents:

- guarded state transition initiating payment intent persisted transactionally,
- queued async notification respecting commit ordering,
- idempotent retry path.

Difference inventory

Enumerate **seven** divergence points Laravel introduces vs Symfony ergonomically affecting test harness shape & failure attribution clarity.
