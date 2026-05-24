# Unit 3 — OOP: interfaces, traits, composition without framework worship

## Outcomes

- **Interfaces survive longer than adapters**: carve boundaries where mocking is honest, not “interface per class ritual”.
- **Traits as mechanical reuse only**: visible behaviour still needs tests; forbid god-trait hierarchies collapsing boundaries.
- **Composition over ornamental inheritance**.
- Understand **Variance** intuitively (`iterable<T>` ergonomics affecting API typing).

## Drill

Enumerate **five** codebase smells where Traits hide dependencies you should expose through constructor contracts.

Interview: Explain when **explicit final classes + narrow interfaces** slow teams down positively versus needless ceremony.
