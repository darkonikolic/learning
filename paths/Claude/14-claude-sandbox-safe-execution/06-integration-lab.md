# Integration lab — sandbox + AI execution

Synthetic stack tying prior units: **Symfony API**, **Go worker**, **MySQL**, **Terraform**, containers, optional cluster snippets.

Deliver **explicit governance artefacts**:

```
 permission model articulated
       → sandbox/container boundary documented
             → secret isolation proven (fake + scoped identities only)
                  → approval flow for infra & schema moves
                         → rollback story for infra + runtime
```

### Deliberate fault injection (disposable env only)

Escalated filesystem permissions  

Accidental-looking secret surfaced in prompts  

Broad network egress enabled  

Dangerous composite shell suggested

Observe whether **your enforcement** detects / refuses / restores—or document gaps brutally honestly.

### Measure

Blast radius before vs after tightening  

Incidents of accidental secret exposure vectors  

Misclassified commands (blocked safe ops vs allowed dangerous ones)

Notebook output: distilled **ALLOW / DENY / ASK_APPROVAL** matrix you will paste into `.cursor/rules` or personal runbooks—maintain consciously.

### Checkpoint mantra

Framing completes when **assistants operate where you constrained them**, under **explicit permissions**, rather than owning your host by default narrative.
