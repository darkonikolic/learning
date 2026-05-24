# Chunking thinking

**Theme:** Documents are sliced for retrieval quality—bad chunks mis-route queries more than mediocre embedding tables.

Contrast:

| Weak | Strong |
|------|--------|
| “Entire Order module pasted” drowning refund nuance | **Ownership chunk** aligning to bounded artefacts: REFUND SPEC excerpt, PAYMENT boundary blurb, RETRY OWNERSHIP note |

Heuristics—not universal laws—for technical corpora chunk design:

Honor **DDD / CQRS seams** splitting aggregates & projections  

Retain **minimal cross-referencing headers** aiding anchor matching  

Preserve **constraints & NFR** chunks distinct from behavioural narrative ones  

Prevent giant vendor dumps unless scope truly integration-wide ephemeral

Symfony practice: hypothetical **DDD ecommerce** knowledge map—articulate deliberate chunk taxonomy before indexing fantasy.  

Go practice: isolate **payment worker** contracts (signals, backoff, ACK invariants).

LAB: Replay one problem triad—**(A)** oversized amalgam chunk **(B)** minimal micro-chunk bombardment lacking context **(C)** balanced boundary-aligned chunk set—critique retrieval signal qualitatively (answers stable? iterations reduced?).

Discuss **risk**: micro-chunks erasing precondition sentences—macro-chunks obscuring contradictory historical paragraph buried mid mass.

Embedding note stays **conceptual** here—density & overlap interplay matters more than chasing model vendor buzzwords blindly.

### Checklist

- [ ] Chunk manifests versioned—or stale chunk boundaries haunt silently during refactors.  
