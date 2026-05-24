# Incremental refactor

**Theme:** **Small change → validate → small change.** Rewrites disguised as “cleanups” are the common senior stumble.

### Anti-pattern vs discipline

**Weak narrative:** Rip out module; hope tests exist.  

**Strong narrative:** Sequenced **step 1 / step 2 / step 3** each leaving the system deployable/releasable (or cleanly behind a guarded flag).

### Assistant guardrail rehearsal

Forbidden vibe: **delete-all / replace-all blueprint** masquerading as refactor. Required vibe: **evolution** preserving behaviour while relocating responsibilities.

### Practice rotations

| Stack | Drill anchor |
|-------|----------------|
| **Symfony** | **Legacy service peel** — extract policy or persistence behind seams one vertical slice at a time. |
| **Go** | **Repository refactor** — interface drift without breaking callers; temporary adapters OK if labelled as debt with removal step. |

### Lab invariant

Rollback thinking piggybacks every intermediate step—even when “only internal” refactor—because internal refactors leak through timing and caching in distributed setups.

### Checklist

- [ ] Steps are **ordering-safe** — each merges without requiring the subsequent step already shipped blindly.  
