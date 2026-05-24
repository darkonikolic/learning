# Unit 3 — CQRS separation without ceremonial dogma

Outcomes

- Command handling single write intent with explicit transaction boundary acknowledgement.
- Read models optimized for UI / API ergonomics—even if Doctrine / Eloquent still backs them pragmatically initially.
- **Bus indirection rationale**: delaying framework-specific handler discovery coupling.

Discuss **Symfony Messenger commands** parallels **Laravel command buses** optionally + event sourcing caution footnote—not mandatory stack leap.
