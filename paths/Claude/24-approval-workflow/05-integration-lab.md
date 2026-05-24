# Integration lab — human-in-the-loop payment platform

Composite stack: Symfony, Go, MySQL, Terraform, Docker, Kubernetes—multi-agent roles as in your prior orchestration practice: Planner, Architect, Implementer, QA, Ops, Reviewer, **Human approver**.

### Required macro workflow

```
 GOAL / TASK
      → agent outputs + CONFIDENCE
            → REVIEW + FEEDBACK cycles
                  → ALIGNMENT freeze
                        → APPROVAL per matrix
                              → EXECUTION
                                    → POST REVIEW + verification ownership
```

### Deliberate fault injections (sandbox)

Wrong or ambiguous **SPEC** snippet  

Bad **routing** (wrong agent leading)  

**Tool fail** / timeout  

**Hallucination** pressure (thin context)  

Attempt to **skip approval** or downgrade matrix level incorrectly

Expected system behaviour:

**Detect** policy or confidence breach  

**Repair** with explicit human feedback  

**Continue** only after realigned approval path—not silent override

### Measure

**Approval correctness** — was the right tier enforced?  

**Feedback quality** — actionable vs vague?  

**Repair quality** — did changes stick in artefacts?  

**Confidence accuracy** — were lows escalated, highs still reviewed where needed?

### Notebook

Where the model was **trusted too much**  

Where **approval** was thin theatre  

What **Rule / Skill** emerged from repetition

**Checkpoint closure:** identity is **AI + human = system**—not assistant monologue with occasional rubber stamp.
