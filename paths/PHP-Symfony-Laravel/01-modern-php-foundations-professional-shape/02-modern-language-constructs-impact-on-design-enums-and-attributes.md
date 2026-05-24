# Unit 2 — Language surface that shapes backend design

## Focus

Treat language features as **design levers**:

- **`enum` backed cases for state**, not sprawling string constants.
- **`Attribute`s** documenting cross-cutting semantics (routing metadata, serialization policy, doctrine mapping discipline) versus anonymous magic conventions.
- **`Generator` iterators**: streaming ingestion with bounded memory; still model **lifetime and exception semantics** (consumer abort mid-sequence vs full materialisation pitfalls).
- **Exceptions as rare control flow**: domain failures often deserve **explicit result types**, not swallowed stack traces everywhere.

## Lab

Specify **three** refactor targets in legacy-style code where:

- enums replace sentinel strings safely,
- an attribute declares one cross-cutting invariant you currently encode in procedural checks.

Deliverable short note on **backward compatibility drift** risks when altering enum cases or widening attribute interpretations.
