# Property testing ownership

**Theme:** Assertions over **rules**, not heroic single-shot examples alone.

Rather than chasing one miraculous input snapshot, articulate **predicates**:

| Policy surface | Sketch property |
|----------------|----------------|
| Retry counter | retries are **never below zero** and never surpass configured ceiling |
| Timeouts configured | durations **never negative** |

### Lab intuition — payment-ish ownership

Enumerate invariants owed to treasury / treasury-adjacent systems before coding generators — property tests amplify once invariants crystallise.

### Concept tags

**Invariant ownership** (you must list them before shrinking tools help)  

**Property testing posture** (`testing/quick` Go style / mature PHP equivalents / external harnesses acceptable)

### Practical guardrail

Generators must stay **controlled blast radius**: cap complexity so failures shrink to comprehensible replay seeds.

### Checklist

- [ ] Predicates cite **pure** domain kernels first (easier shrinking).  
- [ ] Logs print **minimal counterexample artefact**, not oceans of stderr.  
