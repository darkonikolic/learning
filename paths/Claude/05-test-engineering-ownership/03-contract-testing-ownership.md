# Contract testing ownership

**Theme:** Stability at **service edges** — request/response (or event schema) is a contractual obligation owned by somebody.

Sketch:

```
producer shape  ↔  enforced consumer expectations
```

Labs rotate:

| Side | Artefact |
|------|----------|
| **Symfony HTTP API** | Contract tests on handler DTO symmetry + rejection codes |
| **Go worker integrations** | Message contract vs publisher truth |

### Boundary ownership recap

Owning **boundary** implies owning **changelog discipline** — breaking edits require deliberate version bump rituals you document.

### Concept tags

**Contract ownership**  

**Boundary ownership** (overlap with SPEC phase vocabulary — tighten language so both specs and tests cite same glossary fields)

### Checklist

- [ ] Fixtures include representative **illegal** payloads, not golden paths only.  
- [ ] Schema drift alerts land before unrelated teams burn days.  
