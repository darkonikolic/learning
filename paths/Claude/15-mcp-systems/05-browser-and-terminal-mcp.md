# Browser + terminal MCP

**Theme:** Prefer **verification** over guesswork:

**Browser MCP** gathers authoritative **documentation**, changelog nuance (breaking deltas), sometimes UI reproduction evidence.

**Terminal MCP** (or shell-capable equivalents) tails **structured logs**, container states, infra CLIs disciplined by policy—not unconstrained omnipotence.

Practice incident arc (ops worker failure stylised):

```
 terminal log capture & structured filtering
       → corroborative trace artefacts if exported
               → hypotheses ranked before repair attempt
                       → narrowly scoped infra query (docker / compose / kubectl / terraform PLAN only until approval posture satisfied)
```

### Guardrail LAB

Assistants MUST NOT jump to speculative **fix patching** absent prior evidence artefacts—simulate forced pause: summarise observed signals first.

Discuss risk: naive **kubectl/terraform** autonomy—align with staged approval classifications from **your sandbox / CLI policy**.

Browser automation blind spots: iframe lockouts, SSO walls—document blockage instead of tool thrash repetition.

### Checklist

- [ ] Sensitive URLs / internal-only endpoints never screenshot-shared casually—treat viewport captures like log excerpts.  
