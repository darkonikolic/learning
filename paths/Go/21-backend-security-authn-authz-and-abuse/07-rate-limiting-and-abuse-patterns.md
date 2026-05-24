# Unit 7 — Rate limiting & abuse resistance (incl. idempotency abuse angles)

Design limits at edge (gateway) vs app (finer grained) trade spectrum.

Include **idempotency key abuse**: unbounded key cardinality, storage DoS, TTL strategy.

Deliverable: sketch policy for `/payments` endpoint bursts + duplicate retry storm friendliness.
