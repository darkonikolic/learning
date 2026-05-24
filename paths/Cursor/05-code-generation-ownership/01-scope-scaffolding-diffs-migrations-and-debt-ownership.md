# Unit 1 — Scope: code generation ownership — safe acceleration

Mindset shift: generation is **provisional** until integrated, tested, reviewed under human architectural authority.

## Learning outcomes

- **Scaffolding ownership**: templates must align with project conventions (lint, fmt, module layout).
- **Incremental generation**: vertical slices > horizontal carpet refactors.
- **Implementation ownership**: merge author understands every line or has explicit delegation + follow-up learning plan.
- **Architecture & constraint preservation**: guard rails for public API stability, error semantics, logging shape.
- **Compatibility ownership**: semver / DB migration pairing awareness.
- **Migration ownership**: dual-write / backfill / validation windows articulated before code drops.
- **Diff ownership**: readable hunks, logical commit boundaries, bisect-friendly history.
- **Rollback ownership**: feature flags, toggles, revert strategy per risky commit.
- **Boundary preservation**: no silent cross-module leakage “because AI suggested import”.
- **Dependency ownership**: upgrade paths vetted (license, breaking notes, supply chain).
- **Technical debt ledger**: track expedient AI patches → scheduled paydown.
- **Refactor ownership**: behavioural equivalence arguments (tests + invariants).
- **Regression ownership**: expand tests *before* wide automated edits when feasible.
- **Consistency**: generated comment tone / docblocks must not fight house style.

Cross-links: verification cadence **`07-*`**, governance **`06-*`**, failure patterns **`08-*`**.
