# Engineering operating system (EOS)

**Theme:** Merge prior syllabi into a **navigable platform layout** your assistant stack can target predictably.

### Illustrative top-level map (adapt names)

```
 rules/          always-on policy slices (architecture, security, coding, review)
 skills/         procedural SKILL packages (domain + ops + IaC + DB)
 templates/      recurring artefact scaffolds (SPEC, incident, migration plan)
 approval/       matrices + human loop expectations
 security/       threat + AI safety cross-links to Rules
 memory/         ADR / SPEC index discipline
 retrieval/      how knowledge enters context (paths, tools, freshness rules)
```

### Macro runtime flow (idealised)

```
 Problem arrives
       → RETRIEVE grounding (docs, SPEC, logs policy-compliant)
             → select SKILL(s)
                   → RULES constrain generation
                         → AGENTS (if used) follow orchestration + STATE contracts
                               → SECURITY + APPROVAL gates
                                     → implement / review / execute
                                           → EVALUATION updates Rules/Skills
```

**LAB:** Draw **your** actual directory / config mapping to this map—even if some folders live in repo vs personal dotfiles—document where each pillar lives so you stop improvising paths.

### Checklist

- [ ] EOS doc names **owner** for updates (role or human) per subtree—no orphan maintenance.  
