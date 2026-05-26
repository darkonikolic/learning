# Lab: Audit your model assignments

Review how Claude Code picks models for your project, adjust one assignment with documented reasoning, and record the decision on disk.

**Prerequisite:** `task-api/` has `.claude/settings.json` and at least one file under `.claude/agents/` (for example `code-reviewer.md` from module 04).

---

## Step 1: Inspect current configuration

```bash
cat .claude/settings.json
ls .claude/agents/
```

Note:

- Default session model (if set in settings or your `/config` UI)
- Any per-agent model hints in `.claude/agents/*.md` frontmatter or body
- Whether subagents inherit the session default

Model choice lives in product config (`settings.json`, `/config`, optional agent files) — not in a separate planning-tool config file under the repo.

---

## Step 2: Classify each role

Map roles you actually use in task-api to tiers using `18-model-selection/02-when-to-use-which.md`:

| Role | Typical work | Suggested tier |
|------|----------------|----------------|
| Spec / frame | Writing or tightening `docs/specs/*.md` | Opus when ambiguous; Sonnet when template-driven |
| Plan | `/plan` → `docs/plans/<phase>-plan.md` from SPEC | Sonnet |
| Execute | Bounded implementation from approved plan | Sonnet |
| Review | `/code-review`, security pass | Opus |
| Summary / status | Short `docs/state.md` or checkpoint text | Haiku |

Write your current vs recommended table before editing anything.

---

## Step 3: Make two targeted changes

1. **One downgrade:** Opus → Sonnet where inputs are already explicit (planner or executor on task-api-sized work).
2. **One Haiku candidate:** narrow classification or summary task only — not review or spec ambiguity.

Apply changes in `.claude/settings.json` and/or the relevant `.claude/agents/*.md` file. Do not downgrade reviewer or security-review roles to Haiku.

---

## Step 4: Document reasoning

```bash
mkdir -p docs/decisions
```

Create `docs/decisions/model-assignments.md`:

```markdown
# Model assignment decisions

## Date: [today]

## Changes

### [role]: [old] → [new]
**Reason:** one sentence — why the old tier was over-specified.

### [role]: [old] → claude-haiku-4-5
**Reason:** one sentence — narrow output, no multi-step reasoning.

## Unchanged (and why)

### reviewer: claude-opus-4-7
**Reason:** adversarial review; keep highest tier.
```

---

## Deliverable

- Updated `.claude/settings.json` and/or `.claude/agents/*.md`
- `docs/decisions/model-assignments.md`

---

## Checklist

- [ ] I inspected settings and agent files — not a fictional external config path.
- [ ] I classified roles against Opus / Sonnet / Haiku guidance.
- [ ] I made one Sonnet downgrade and one Haiku change with justification.
- [ ] Reviewer / security roles stayed on Opus (or equivalent top tier).
- [ ] Reasoning is recorded in `docs/decisions/model-assignments.md`.
