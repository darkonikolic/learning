# Unit 07 — Deadlock choreography and mitigation

Two sessions acquire locks in opposing order on `orders` vs `inventory`; force engine deadlock detection.

Discuss prevention: consistent lock acquisition ordering, smaller critical sections, backoff / retry strategy at app layer.
