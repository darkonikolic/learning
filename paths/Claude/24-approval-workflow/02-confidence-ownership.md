# Confidence ownership

**Theme:** Assistants **do not always know**—the system must surface **confidence** and route uncertainty to humans before costly execution.

### Bands (example rubric—tune to your risk appetite)

| Band | When to use | Typical action |
|------|-------------|----------------|
| **High** | Narrow, verifiable fact against local code or pinned docs (e.g. Go pointer rule in a file you opened) | May proceed with normal review; still verify for deploy class. |
| **Medium** | SPEC or DDD boundary interpretation with room for product nuance | Human review on design/architect hop before implement. |
| **Low** | Production incident with **insufficient logs**, ambiguous symptoms, or cross-system guesswork | Stop for data collection, escalation, or explicit “no execute” until confidence rises. |

### Workflow discipline

```
 CONFIDENCE assessed candidly
        → THRESHOLD rules (what level may auto-continue vs must stop)
                → HUMAN ESCALATION path with minimal repro bundle
```

**Practice sketches**

Symfony **DDD boundary** contention—medium default until product owner confirms language.  

Go **distributed retry** cross-layer story—medium/high split: code-local vs cross-service contract.  

**Ops latency** mystery without traces—low until observability completes.

**LAB:** For each assistant answer in exercises, tag **confidence** + one-line justification—refuse to treat untagged output as ready for execution.

Discuss **verification ownership**: human or designated role upgrades confidence after independent checks—not self-graded model optimism.

### Checklist

- [ ] Low-confidence paths have a **written “do not execute”** default for deploy-class actions.  
