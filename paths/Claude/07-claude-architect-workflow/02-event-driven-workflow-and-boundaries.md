# Event-driven workflow and boundaries

**Theme:** The architect owns **how the system progresses through process** — especially when work is **asynchronous** and **event-led**.

Sketch (example — tailor to your platform):

```
request / command accepted
    → validation & policy gates
        → durable intent recorded
            → payment / settlement choreography
                → inventory / saga compensations where needed
                    → outbound notifications / integration events
                        → audit & observability checkpoints
```

**Event-driven stance:** transitions publish **facts** bounded contexts subscribe to via **explicit contracts** (see contract-testing habits from Phase 3.5 where relevant).

### Boundary ownership reminder

Edges must state **producer owner** and **consumer owner**; drifting vocabulary between specs, tests, and events is architectural debt.

### Ops workflow complement

```
change validation windows
    → artefact backups / checkpoints acceptable to policy
        → phased deploy
            → health & SLO-aligned checks
                → guarded rollback doorway
```

## Lab mandate

Produce **diagram + narrative** of the workflow **before** implementation-heavy answers when pairing with Claude on this curriculum.

### Checklist

- [ ] Events / messages named as **past-tense facts** where that matches your modelling style.  
- [ ] Duplicate delivery and reordering hazards called out **at boundaries**.
