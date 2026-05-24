# Unit 1 — Scope: context engineering — context *is* design

Mindset shift: optimise **instruction + corroborating evidence bundles** deliberately — not shovel entire repos into chats.

## Learning outcomes

- **Context ownership**: who constructs, refreshes, and retires ephemeral instruction state.
- **Prioritisation heuristics**:
  - Symptom → nearest failing test → callee stack → owning module.
  - Feature → contract first → adapters second → internals last.
- **Layering blueprint**:
  1. **Goal / invariant**
  2. **Pinned evidence** (file paths, excerpts, profiler snapshot)
  3. **Operating constraints**
  4. **Forbidden moves**
  5. **Verification plan**
  6. **Rollback / checkpoints**
- **Compression discipline**: summarise large regions with **anchors** (symbols, hashes) referencing repo truth — forbid narrative-only invention.
- **Retrieval mindset**: treat search tools as stochastic — cross-check grounding (open file excerpt > memory).
- **Instruction hierarchy**: precedence when layers conflict (“security constraints override ergonomics refactor”).
- **Context budgeting**: approximate token-ish weighting — escalate summarisation triggers.
- **Memory / persistent artefacts**: Cursor rules, SKILL files, AGENTS stubs — versioning + staleness auditing.
- **Session ownership**: when to fork new chat vs continue polluted thread.
- **Dependency context hygiene**: pinning library versions constraints for assistant suggestions referencing APIs.
- **Architecture preservation snippets**: capsules of ADR excerpts + diagram snapshot lines.

Adjacent work: overlaps **`04-*`** (prompt shapes) **`19-*`** (cost) **`12-*`** (workflow minimalism anti-patterns).
