# Drift detection

**Theme:** Implemented reality diverging silently from authoritative SPEC—**spec drift**—is a first-class outage class.

### Stereotypical slips

SPEC: `retry = 3` • Code/env: infinite / unbounded loop  

Doctrine / config default overrides narrative spec  

Symfony aggregate invariants verbally “remembered”—never mirrored in invariant tests  

Rabbit topology diverges (queue naming, TTL, DLQ binding) versus the documented topology.

### Validation + repair workflow

```
 implement under frozen SPEC excerpt
                          → automate / script VERIFY where cheap
                                                                   → DIFF numeric + behavioural fields vs SPEC table
                                                                              → classify DRIFT severity
                                                                                                     → repair code OR repair SPEC consciously (ownership + versioning)
                                                                                                                      → rerun verification gates
```

**Practice**

Go **distributed retry** layers dissected independently—transport vs domain.  

Symfony **DDD aggregate** behavioural patch—replay invariant checklist after each edits wave.

Mandatory lab arc: deliberate **implement → verify → find drift → repair** cycle—not stop at green compile.

Discuss **evaluation hooks**: drift counts feed evaluation systems dashboards—trend downward as platform matures.

### Checklist

- [ ] When code is “right” and spec wrong—**SPEC gets version bump** acknowledging correction, never silent stealth rewrite only in chat.  
