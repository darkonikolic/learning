# Spec evolution + drift

**Theme:** Living systems rearrange truths — SPEC must evolve **with rationale** or implementation will silently diverge.

## Evolution rehearsal

Historical narrative pattern:

**SPEC baseline:** synchronous payment acknowledgement.  

**SYSTEM shift:** asynchronous settlement path required.  

**SPEC duty:** changelog entry — drivers, migrating acceptance, deprecated bullets.

## Detecting spec drift

**Symptoms:**

- Implemented retry loop violates **bounded retry SPEC** (“infinite-ish”).  
- Timeouts vanished relative to mandated maximum connect time in SPEC.  

**Process:**

1. Extract **golden SPEC excerpt** unchanged from prior baseline.  
2. Diff behavioural claims in implementation/design doc.  
3. Mark **violations**.  
4. Either **repair code** toward SPEC or — better when reality changed — **revise SPEC** with traceable history.

## Lab

Produce **before/after SPEC delta** prose for each intentional evolution; run a Claude-assisted **SPEC compliance sweep** referencing stored acceptance bullets.

## Checklist

- [ ] SPEC version or date stamp increments when behavioural truth moves.  
- [ ] Violations categorized: **truth changed** vs **engineering mistake**.  
