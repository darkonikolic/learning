# Retrieval thinking — framing

## Phase framing — Retrieval Systems (“Phase 7.7”)

**Units in this folder:** `01`–`05` (topic order only).

### Mindset pivot

Away from shoveling whole repositories or dumping “every document we have.” Toward **governed retrieval**: what knowledge is truly required—then fetch **only relevant**, validate fit, repair when retrieval lies.

Comfort at scale: stacks like **Symfony**, **Go**, **Terraform**, **Kubernetes**, **MySQL** coexist with **dozens of specifications**—the successful pattern is selective retrieval, **not** “load everything.”

### Practice choreography (architecture-oriented)

```
 Canonical docs / internal knowledge base artefacts
           ↓ assisted retrieval orchestration (“Claude retrieves” deliberately)
                       ↓ architect-grade answer anchored in cited snippets
```

This area complements **structured project memory**: retrieval is **how** bounded truth enters working context without flooding it.

### Theme map

**RAG** as pattern (retrieve → augment reasoning)  

**Retrieval pipelines** — ingest, chunk, embed (conceptually), index, query, rerank, fuse  

**Chunking strategies** respecting ownership boundaries  

**Embeddings / semantic retrieval** understood qualitatively (vectors approximate intent; they err)  

**Hybrid retrieval** lexical + semantic merges  

**Reranking** & quality scoring  

Cross-cutting **knowledge ownership**, **quality habits**, **retrieval debugging**

### Claude Retrieval Template — for substantial tasks

| Field | Holds |
|-------|-------|
| **PROBLEM** | Slice of work + constraints—not the entire platform at once. |
| **KNOWLEDGE NEEDED** | Bullet list of artefacts / facts/classes still absent from working context. |
| **KNOWLEDGE SOURCE** | Where truth lives path, doc ID, MCP tool tier, authoritative external manual section class. |
| **RETRIEVAL STRATEGY** | lexical vs semantic vs hybrid; filters (namespace/tag); breadth budget. |
| **RETRIEVAL RISK** | Staleness class, synonym collision, ambiguous module names—pre-declared traps. |
| **VALIDATION** | Checks that snippets actually answer hypotheses / align with SPEC—not vibes. |
| **REPAIR** | If validation fails—re-query, re-chunk framing, escalate human clarification. |

**Checkpoint mantra:** Claude does not merely “have context”; Claude **runs a deliberate knowledge pipeline** you design.

Sandbox / MCP layers still enforce permissions—retrieval widening must not pierce secrecy rules.

---

**LAB — unit invariant**  

Before engaging an assistant heavily, standalone **Knowledge needed** list—Symfony **refund ownership**, Go **worker retry doctrine**, infra **Terraform drift investigation** vignettes—as reusable rehearsal.

### Checklist

- [ ] Every retrieval-driven answer names **sources used** succinctly—even if informal path references.  
