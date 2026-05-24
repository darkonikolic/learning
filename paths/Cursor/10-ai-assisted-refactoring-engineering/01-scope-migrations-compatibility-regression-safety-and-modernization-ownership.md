# Unit 1 — Scope: AI-assisted refactoring — disciplined change at scale

Mindset shift: refactors are **inventory + safety harness** first; completions are last-mile once invariants locked.

## Learning outcomes

- **Refactor ownership framing**: behaviour preservation arguments.
- **Migration ownership** (code + data + config) with explicit phases.
- **Compatibility & contract preservation** when public surfaces exist.
- **Technical debt quantification** heuristic (interest vs principal payments).
- **Architecture alignment checks** against target-state sketches.
- **Regression prevention playbook**: widen tests BEFORE mechanical edits where feasible.
- **Dependency cleanup rationale** (death of dead modules, unify duplicate helpers cautiously).
- **Constraint preservation** during mechanical rename waves.
- **Rollback discipline**: bisect narratives, checkpoints, tagging.
- **Large-scale refactoring sequencing**: strata (types → internals → callers) minimise broken intermediate states when possible.
- **Legacy modernization** trade-offs (strangler façade vs big-bang condemnation).
- **Change safety RACI-lite** pairing IC + reviewer expectations.

Linkage: reinforces **`05-*`**, validates via **`07-*`**, discovers via **`09-*`** prior mapping.
