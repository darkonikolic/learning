# Rule conflict resolution

**Theme:** Rules collide—**simplicity** vs **future scale**, **velocity** vs **security**. The platform needs an explicit **priority stack**, not improvised debate each incident.

### Suggested priority ladder (tune deliberately)

```
 Security
     ↓
 Correctness
     ↓
 Reliability / safety of change
     ↓
 Maintainability
     ↓
 Performance / cost optimisation
```

When two Rules conflict:

1. Classify conflict type (risk vs ergonomics vs style).  

2. Map each side to ladder position.  

3. **Higher-tier wins** unless you document **exception ticket** / ADR overturn with named approver.

**LAB:** Write **minimum ten miniature conflict scenarios** (tabletop—“Rule A vs Rule B”) and record **resolution citing priority ladder**.

Examples: “never log PII” vs “debug verbosity”; “minimal dependency” vs “battle-tested crypto lib”; “ship today” vs “migration safety expands contract”.

### Output artefact encouragement

Maintain `RULE_PRIORITY.md` (name illustrative) referencing stack + exception process—helps assistants and humans stay aligned.

Discuss **Skills** reading same priority doc—Skills must not silently invert ordering.

### Checklist

- [ ] Exceptions are **time-bounded** or **ADR-linked**—not permanent silent overrides.  
