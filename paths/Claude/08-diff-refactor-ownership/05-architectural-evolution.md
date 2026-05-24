# Architectural evolution

**Theme:** **Today ≠ tomorrow blueprint dump.** Produce an honest bridge: motivations, phased risks, sequenced seams.

Diagram narrative you rehearse aloud:

```
AS-IS (truthful constraints)
    → TO-BE target topology (narrow initial slice plausible)
          → bridging migrations + toggles / strangler seams
```

#### Example hinge

Present: **modular-ish monolith** handling payments + notifications intertwined. Horizon: clearer **event-driven** boundaries—but only through **measurable intermediate states** reducing dual-write eras.

### Practice rotations

| Stack | Drill |
|-------|-------|
| **Symfony** | **Modular monolith tightening** — package boundaries enforcing dependency direction gradually. |
| **Go** | **Worker extraction** — carve bounded process without instant network fan-out entropy. |

### Assistant expectation

Articulate **WHY NOW**, quantify **risk classes**, expose **ordering of steps**. Ban hand-wavy miraculous cutovers unless you explicitly spike them as throwaway proofs first.

### Checklist

- [ ] Intermediate architecture states each **shrinks** behavioural ambiguity—not only file moves.  
