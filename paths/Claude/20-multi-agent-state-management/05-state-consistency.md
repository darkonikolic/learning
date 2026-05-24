# State consistency

**Theme:** Many agents, **one coherent story**—detect **divergence** before it becomes production drift.

Stereotypical conflict:

Architect state: authoritative backing store **Redis** for a read model  

Implementer substitutes **in-process memory cache** for speed  

QA re-reads SPEC still saying **Redis**—three “truths” now compete

### Consistency habits

Periodic **cross-field diff**: Architect digest vs Implementer config vs QA acceptance checklist  

Explicit **technology tokens** (product names, max retries, TTLs) in shared state—not synonyms  

**CONSISTENCY CHECK** gate before merge or deploy: scripted or human checklist signed

**Synchronisation**: when shared state updates, downstream local states must either refresh or invalidate—stale caches in **human workflow** mirror stale caches in systems.

### LAB

Intentionally create a **forked state narrative** (two conflicting artefacts). Run a consistency pass; reconcile via SPEC update **or** code rollback—not silent “meet in the middle.”

### Checklist

- [ ] After reconciliation, **one** authoritative line exists in SHARED STATE—orphan alternatives deleted or labelled historical.  
