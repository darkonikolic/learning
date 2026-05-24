# State contract and context propagation

**Theme:** The common failure is **half a constraint crossing the wire**—downstream agents fill gaps with confident wrong defaults.

Classic slip (user’s example class):

Shared intent: **retry = 3** (Architect / SPEC)  

Implementer applies **infinite retry** because only the word “retry” propagated—**numeric contract** missing.

### State contract content (minimum across critical edges)

Frozen **SPEC** pointer + excerpt for behavioural numbers  

**Constraints** (timeouts, idempotency keys, ordering) as explicit fields—not prose fluff  

**Boundary** ownership (which aggregate / service owns the decision)  

**Risk** carry-over (what must not regress; what is still unknown)

**Handoff ownership:** sender attests “contract complete”; receiver refuses to implement if any mandatory field is blank.

### Practice

Go **distributed retry**: contract must state transport vs business retry layers separately.  

Symfony **CQRS aggregate**: command vs projection invariants travel as named bullets, not implied from folder names.

**LAB:** every handoff document includes a **STATE CONTRACT** mini-block—even two lines beats implicit myth.

### Checklist

- [ ] Numeric and enum-like decisions **never** travel as vague adjectives (“aggressive retry”) without bound.  
