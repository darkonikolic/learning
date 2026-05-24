# Unit testing ownership

## Phase framing (Test Engineering Ownership)

**Phase numbering:** topical track **`01`–`06`** (topic order).

### Working pipeline (closes the loop each increment)

```
Specification  →  Implementation  →  Test  →  Verification  →  Repair
```

**Verification ownership:** you certify evidence **against acceptance + risk appetite** — green CI alone ≠ finished if claims about safety/scalability stay unexamined.

**Regression ownership:** when behaviour changes, owning **who updates / deletes which tests**, and guarding against orphan assertions.

**Test pyramid stance:** biased toward **cheap fast foundational tests** widening toward costlier strata only when seams demand them — Claude should not hallucinate pyramid inversions casually.

**Failure ownership:** surfaced defect → reproducible specimen → characterised root class → guarded test added or explicitly waived debt.

### Mindset pivot

| Old comfort | Owned comfort |
|-------------|---------------|
| “It runs / looks fine” ⇒ done | SPEC-backed change **implemented ⇒ verified ⇒ stressed (where owed) ⇒ repaired knowingly** |

### Exit bar for stacks in this lane

Fluent loop across realistic slices:

```
Symfony ⇄ persistence expectations

Go service / worker logic ⇄ behavioural truth

Queues + DB interplay where your architecture demands it
```

Claude-assisted systems must articulate **why** artefacts look safe-enough plus **scalability caveats**, not shrug “passes smoke”.

### Theme inventory carried across numbered units

**Unit • Integration • Contract • Property • Chaos • Load** modalities plus pyramid + verification/regression/failure ownership consciousness.

---

**Theme:** Behaviour-level proof — deterministic, narrowly scoped assertions about domain rules.

### Symfony cue

**CQRS aggregate** kernels: mutations + invariants + rejection paths surfaced as succinct PHPUnit (or successor) suites — avoid testing framework plumbing instead of business law.

### Go cue

**Worker/business helpers** devoid of flaky clock/network — deterministic clocks & DI seams so retry math is honest.

### Suggested labs (mix & match)

Refund orchestration branching  

Retry backoff edge math  

Aggressive validator permutations rejecting illegal domain states sooner than integration stage

### Concept tags surfaced now

● **unit test posture** ● **deterministic verification**

### Checklist

- [ ] Each test cites **business rule headline** mirrored from SPEC lineage.  
- [ ] Forbidden randomness sans explicit seed rationale.  
