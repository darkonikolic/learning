# Integration lab — payment platform durable state thread

Synthetic long arc: Planner goal → Architect tradeoffs → Implementer edits across **Go + Symfony + DB migrations** → QA spec validation → Ops rollback rehearsal.

Orchestration must demonstrate:

**State share** — shared artefacts updated deliberately  

**HANDOFF** — each edge with STATE CONTRACT completeness  

**RECOVER** — at least one rehearsed interruption and resume path  

**CONTINUE** — final state matches acceptance without ghost assumptions

### Measure (qualitative + counts if you track them)

Incidents of **state loss** (missing field discovered late)  

**Repair** cycles to align divergent views  

**Handoff quality** — did the next agent repeat discovery work needlessly?  

**Consistency** pass outcomes — conflicts found pre-merge vs post-merge

### Notebook deliverables

Where **context disappeared** (which field, which hop)  

Where **ownership** blurred (two writers, no merge rule)  

Where **state model** was underspecified (fix your template next iteration)

**Checkpoint closure:** narrative identity is **durable AI workflow**—continuity is engineered, not hoped for.
