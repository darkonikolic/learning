# Anti-patterns

Things to NOT do. Each has a trigger and the correct move instead.

- **Editing trace files when only a chat review was requested.** → Report in chat; edit only on explicit request.
- **Writing pacing/time (hours, weeks, per-day) into trace `.md`.** → Keep pacing in chat only.
- **Over-engineering the system** (50 rules / 30 agents / 100 skills). → Keep the set small and maintainable.
- **Auto-agreeing with the user** to be agreeable. → Validate first (`reality-guard`).
- **Adopting a new rule from a single frustrated correction.** → Treat feedback as data; require recurrence + evidence before changing a rule.
- **Auto-translating or converting dialect in existing traces.** → `project-A` stays Serbian (ekavica); don't translate or change dialect without asking.
- **Leaving empty/stale structure** (empty dirs, contradictory module lists). → Fill with real content or remove; keep orientation lists truthful to the actual folders.
