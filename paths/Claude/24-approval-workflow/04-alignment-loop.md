# Alignment loop

**Theme:** Optimise the **process**, not a single answer: repeat until human and agents share the same **task**, **constraints**, and **risk** story.

### Loop structure

```
 TASK framed
      → agent proposal
            → human REVIEW
                  → FEEDBACK
                        → REPAIR
                              → repeat until ALIGNMENT + APPROVAL gates clear
```

**Practice threads**

Symfony **refund flow**—align aggregate vs integration boundaries before coding churn.  

Go **payment worker**—align retry semantics with ops SLO language.  

**Incident** response—align “what we know” vs “what we assume” before infra changes.

**LAB deliverable:** short log answering:

What **repeated** across iterations (smells like missing Rule or Skill)?  

What deserves a **Rule** update vs one-off instruction?  

What deserves a **Skill** (repeatable procedure) vs ad-hoc doc?

This closes the gap between one-shot chat and **durable workflow engineering**.

### Deployment approval note

Alignment is **not** approval: you can agree and still block execute until **deployment approval** policy satisfied—separate explicit gate.

### Checklist

- [ ] After alignment, **SPEC or task brief** is updated so the next session does not restart from zero.  
