# Retrieval debugging

**Theme:** Pipelines malfunction like code—observe outputs, hypothesise retrieval layers, shorten feedback loops ethically.

Representative breakage narratives:

Architectural advice mirrors **obsolete ADR snapshots** SPEC explicitly superseded—but old chunk rank dominated.  

Model **ignores ingested grounding** absent validation hooks—looks authoritative while hallucinating glue.  

**Wrong module embeddings** victorious due to lexical collision or partial filename overlap (“payment” drowning “payout reversal” distinctions).

Debugging macro-workflow mimic:

```
 surface RESULT unsatisfying / contradictory
       → cite KNOWLEDGE SOURCES actually surfaced
               → scrutinise retrieval step (filters, chunk boundaries, synonym collapse)
                           → VALIDATION experiments (narrow re-query variants)
                                           → REPAIR (re-ingest excerpt, annotate chunk header, escalate human clarifier prompt)
```

LAB: ethically craft **incorrect retrieval precondition** sandbox—simulate stale embeddings index OR maliciously broad synonym tag—observe detection discipline (assistant must classify failure class before patching).

Enumerate repairs:

Query reformulation choreography  

Boost / penalty metadata layering on ownership tags  

Hybrid fallback toggling lexical rescue when semantic confidence low  

Potential partial **rerank** heuristics (even manual human rerank rehearsal educates intuition)

Security angle: poisonous doc injection awareness when multi-tenant corpuses share index—assume least trust boundary.

### Checklist

- [ ] Each rehearsal logs at least **one preventive structural ingestion tweak**—not only ephemerally “asked nicer.”  
