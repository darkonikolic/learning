# Lab: Audit your GSD config for model assignments

This lab walks through reading `.planning/config.json`, evaluating the current model assignments, and making one targeted change with documented reasoning.

**Prerequisite:** You have a `.planning/` directory from either the module 21 lab (bootstrapped from scratch) or from running GSD on an existing project.

---

## Step 1: Open config.json and find the model profile section

```bash
cat .planning/config.json
```

Look for a section that controls model assignments. It will resemble one of these patterns, depending on your GSD version:

```json
{
  "model_profile": {
    "research": "claude-opus-4-7",
    "planner": "claude-sonnet-4-6",
    "executor": "claude-sonnet-4-6",
    "reviewer": "claude-opus-4-7",
    "summarizer": "claude-sonnet-4-6"
  }
}
```

or

```json
{
  "agents": {
    "discuss": { "model": "claude-sonnet-4-6" },
    "plan": { "model": "claude-sonnet-4-6" },
    "execute": { "model": "claude-sonnet-4-6" },
    "review": { "model": "claude-opus-4-7" },
    "spec": { "model": "claude-opus-4-7" }
  }
}
```

The exact structure varies by GSD version. Find the section — it will be there.

If config.json does not have a model profile section, GSD is using defaults. Note that and continue to Step 2 — you will add a model profile section.

---

## Step 2: Classify each assignment

For each agent type in the config, answer: is this assignment appropriate given the task type?

Use the decision table from `22-model-selection/02-when-to-use-which.md` as your reference.

Write your classification on paper or in a scratch note before touching the file. Example for a typical default config:

| Agent | Current model | Appropriate? | Notes |
|-------|-------------|-------------|-------|
| research | claude-opus-4-7 | Yes | Synthesis of ambiguous inputs |
| planner | claude-sonnet-4-6 | Yes | Clear requirements to PLAN.md structure |
| executor | claude-sonnet-4-6 | Yes | Code generation from defined tasks |
| reviewer | claude-opus-4-7 | Yes | Adversarial quality check |
| summarizer | claude-sonnet-4-6 | Maybe | Could use Haiku — see step 3 |

---

## Step 3: Identify one place to downgrade to Sonnet from Opus

Look for an agent that is currently Opus but whose task type is clear-input, defined-output work. Common candidates:

- A "spec" agent that writes SPEC.md for simple phases (GET /tasks is not complex — Sonnet suffices)
- A "discuss" agent that gathers phase context through structured questions (adaptive questioning, clear inputs)
- Any agent labeled "verify" or "check" that runs defined acceptance criteria — not open-ended judgment

For task-api specifically: if your config uses Opus for the planner or executor, that is unnecessary — both phases have clear requirements and produce defined artifacts.

Make note of the one change you will make.

---

## Step 4: Identify one place where Haiku would be appropriate

Look for an agent that produces a summary, a classification, or a short lookup response. Good candidates:

- "summarizer" agent (milestone-summary, context summaries)
- Any agent that classifies task status (complete/incomplete/blocked)
- Any agent that generates a short status report from existing artifacts

For task-api: the milestone-summary agent is a safe candidate for Haiku. Summarizing completed phase artifacts does not require multi-step reasoning.

---

## Step 5: Make the changes and document reasoning

Edit `.planning/config.json` to apply your two changes (one downgrade from Opus, one change to Haiku).

Then create `docs/decisions/model-assignments.md`:

```bash
mkdir -p docs/decisions
```

Write the file with this structure:

```markdown
# Model assignment decisions

## Date: [today's date]

## Changes made

### [agent-name]: [old model] → [new model]
**Reason:** [one sentence explaining why the old assignment was over-specified for this task type]

### [agent-name]: [old model] → claude-haiku-4-5
**Reason:** [one sentence explaining why this agent's task type is narrow enough for Haiku]

## Retained assignments

### reviewer: claude-opus-4-7
**Reason:** Adversarial review requires deeper reasoning; Opus finds issues Sonnet misses.

### [any others retained at current tier]
**Reason:** [brief justification]
```

Fill in the actual agent names and models from your config.

---

## Deliverable

Two files changed:
- `.planning/config.json` — model assignments updated
- `docs/decisions/model-assignments.md` — reasoning documented

One sanity check: re-read your changes and verify the reviewer and security-audit agents are still on Opus. These should not be downgraded. If you changed them, revert those changes before committing.

---

## Checklist

- [ ] I found the model profile section in config.json (or noted its absence).
- [ ] I classified each assignment as appropriate or over-specified.
- [ ] I identified and made one downgrade from Opus to Sonnet.
- [ ] I identified and made one change to Haiku for a narrow task type.
- [ ] I documented the reasoning in docs/decisions/model-assignments.md.
- [ ] Reviewer and secure-phase agents are still on Opus.
