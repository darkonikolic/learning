# Workflow ownership

**Theme:** The architect stance asks **how work flows through the system and organization**, not only *what widgets to crank out*.

## Pattern

Enumerate **states / transitions people and software traverse** until value is evidenced.

### Go — checkout-esque illustration

ASCII discipline example:

```
request ingress
  → validation gates
       → payment attempt cluster
           → inventory settlement / saga compensation decisions
               → outbound notification fan-out
                   → immutable audit anchors
```

### Ops — lifecycle illustration

```
pre-deploy validations
   → infra backup / checkpoint policy
       → rollout wave
           → layered health affirmation
               → guarded rollback doorway if signals regress
```

## Lab mandate

Produce **diagram + narrative captions** documenting workflow **prior** to code-dense answers when using Claude collaboratively.

### Concept tags embedded here

● **workflow ownership** (you articulate transitions, not incidental micro-tasks scattered ad hoc)

## Checklist

- [ ] Every arrow names **ownership + artefact exchanged** across it.  
- [ ] Forbidden “magic step” jargon — unexplained leaps get numbered unknown risks.  
