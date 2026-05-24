# Shared state ownership

**Theme:** Decide **what everyone must read from the same source** versus what stays **persona-local**—confusing the two creates silent forks.

### Shared state tier (typically versioned paths or ticketing anchors)

Unified **project context** digest (narrow, not raw repo dumps)  

Rules / governance pointers (workspace policy, Sandbox constraints)  

**Architecture snapshot** authoritative for this epic (diagram + boundary list links)  

**SPEC** excerpts with ids / headings  

Explicit **NFR / SLO** bullets that gate acceptance

### Local state tier (explicitly ephemeral or non-binding until promoted)

Planner’s **dependency graph** scratchpads  

Architect-exclusive **tradeoff matrices** staged before freeze  

QA **test matrix drafts** not yet aligned to shared SPEC

When local state **mutates** shared truth, it must go through a **promotion** step (handoff + consistency check)—never direct overwrite of shared narrative by side chat.

### Practice slices

Symfony **refund flow** epic: list which diagrams and SPEC sections sit in **shared** vs which exploration notes stay **local** until Architect signs off.  

Go **payment worker**: shared state names retry contract source; local state holds experimental timing tables until merged into SPEC.

**LAB deliverable:** table **shared vs private state** with **writer role** per row (who may change what).

### Checklist

- [ ] Shared state has a **single writer rule per artefact class** at a time—parallel silent edits treated as a bug.  
