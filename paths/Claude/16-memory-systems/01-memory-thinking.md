# Memory thinking — framing

## Phase framing — Memory Systems (“Phase 7.5”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

Away from imagining “the model simply remembers.” Toward **you** designing working context, persisted artefacts, retrieval paths, staleness hygiene, and **ownership** across long arcs (Symfony ↔ Go ↔ MySQL ↔ Terraform ↔ Kubernetes).

Operational spine you reuse:

```
 Context packaging  →  Memory placement (tier choice)  →  Retrieval choreography  →  Compression / eviction discipline
```

### Memory tiers — vocabulary aligned with cognition literature (used pragmatically here)

| Tier | Holds |
|------|-------|
| **Working** | Immediate task framing, ephemeral scratch—what must be prime *right now*. |
| **Episodic** | What happened chronologically across sessions/incidents/decisions—“we tried X”. |
| **Semantic** | Durable truths about **the system**—bounded contexts, invariants, architecture intent. |
| **Persistent rules** | Non-negotiables you store outside the ephemeral window (**Rules**, runbooks, versioned SPEC, ADRs). |

Cross-cutting tensions the rest of this area tackles: **retrieval**, **compression**, **summarization**, **invalidation**, **memory security** (secrets must never enter durable “memory”), **context decay**, **retrieval ownership**, **knowledge freshness / versioning**.

### Claude Memory Template — for larger tasks

| Field | Holds |
|-------|-------|
| **WORKING MEMORY** | Task goal, hypotheses, pointers to artefacts—minimal tokens. |
| **EPISODIC MEMORY** | Recent decisions/commits/incidents summaries with dates/refs. |
| **SEMANTIC KNOWLEDGE** | Architecture & domain anchors (CQRS seams, aggregates, infra topology). |
| **PERSISTENT RULES** | Citations into repo truth (Rules, SPEC ids, playbook paths)—not recreated inline. |
| **KNOWLEDGE NEEDED** | External or internal lookups still missing before implementation conviction. |
| **RETRIEVAL PLAN** | Where you will fetch each needed fact (filesystem path, MCP tool class, docs URL class). |
| **STALE KNOWLEDGE RISK** | Explicit guess what might be outdated (“library default changed”) + verify step. |

**Checkpoint mantra:** Claude does not “have context” magically—you supply a **deliberate knowledge system** with versioning awareness.

Integration with **sandbox / MCP** tooling: persisted memory artefacts still obey scope and secrecy rules—never hydrate sensitive tokens into summaries.

---

**LAB (unit 01)**  

For representative slices—Symfony **refund** narrative, Go **payment** worker saga, hypothetical **Ops incident** retrospective—annotate each task with what belongs to **working / episodic / semantic / persistent**.

### Checklist

- [ ] Every long arc names an **official source of semantic truth** distinct from conversational drift.  
