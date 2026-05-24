# Skills engineering

**Theme:** **Rule ≈ how you constrain behaviour.** **Skill ≈ what procedure you execute** inside those constraints—with inputs, workflow, outputs.

### Anatomy of a Skill (conceptual)

| Part | Holds |
|------|-------|
| **Name / intent** | e.g. “Symfony Architect slice” |
| **Input contract** | e.g. “payment flow slice + links to SPEC” |
| **Workflow** | Ordered steps (boundary → ownership → CQRS shape → tradeoff → risk → failure modes). |
| **Output contract** | e.g. “SPEC delta, architecture note, implementation plan skeleton” |

Example shape the user hinted:

Skill: **Symfony Architect** — Input: named flow → Steps: boundary, ownership, CQRS, tradeoff, risk, failure → Outputs: SPEC-style artefact + plan hints.

### Authoring targets (minimum set to draft):

`symfony-architect`  

`go-backend`  

`ops-debug`  

`terraform-review`  

`mysql-review`

**LAB:** Invoke work **by Skill reference**—“run X skill with input Y”—rather than dumping a wall of bespoke prompt text each time. Skills should compose with your **Rules** automatically (Rules load as background policy).

Discuss **reusable validation**: bake checklist gates into Skill OUTPUT section (links to acceptance ids, rollback note, observability expectation).

Discuss **Skills vs giant prompts**: Skill is maintainable modular procedure doc—not one-off masterpiece paste.

### Checklist

- [ ] Each Skill names **explicit non-goals** (what this Skill refuses to bypass—e.g. unapproved applies).  
