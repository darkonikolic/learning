# When to use which model

Decision rules for model selection. Each rule has a reason — knowing the reason lets you apply the rule to situations not covered here.

---

## Use Opus when

**Planning phases with high ambiguity.** If you cannot write a one-sentence success definition for a phase, the phase is ambiguous. Opus handles ambiguous inputs better than Sonnet — it is more likely to surface the ambiguity, ask clarifying questions, or structure the problem before committing to a plan. Sonnet on an ambiguous input tends to pick an interpretation and proceed, which produces confident but potentially wrong output.

**Spec writing for complex domains.** Writing SPEC.md for an endpoint with cross-cutting concerns (validation + auth + rate limiting + pagination + error format) requires holding many constraints simultaneously. Opus's reasoning depth handles this better.

**Adversarial review.** `/gsd:code-review` and `/gsd:secure-phase` benefit from Opus because the model is actively trying to find problems. Reviewer agents using Sonnet are less thorough — they find obvious issues but miss subtle ones.

**Security audit.** Threat modeling requires considering attack vectors the implementer did not think of. Opus is more likely to consider second-order effects and uncommon paths.

---

## Use Sonnet when

**Executing plans.** Writing Go handler code from a SPEC, generating test files from acceptance criteria, implementing a route — these tasks have clear inputs and clear expected outputs. Sonnet handles them well at lower cost and faster speed.

**Standard discuss → plan flow.** When the phase intent is clear (you can describe it in two sentences), discuss-phase and plan-phase with Sonnet produce adequate quality. The planning structure (PLAN.md with waves and tasks) does not require Opus-level reasoning when the requirements are already clear.

**Most day-to-day Claude Code work.** Answering questions about your codebase, explaining a function, generating a config file, writing a README section — Sonnet is the right default.

---

## Use Haiku when

**Quick lookups.** "What HTTP status code does 'created' map to?" — Haiku.

**Summarizing long files.** "Give me a three-sentence summary of this 800-line file" — Haiku can do this reliably and cheaply.

**Classification tasks.** Tagging, categorizing, routing decisions where the answer is a label from a known set — Haiku. Example: classifying error log lines by severity before writing them to a report.

**Cost-sensitive batch operations.** If you are processing many files or items and each operation is simple, Haiku reduces cost significantly without meaningful quality loss. The constraint: each individual operation must be narrow and well-defined.

---

## The two-sentence rule

If you can describe the feature in two sentences with no caveats, use Sonnet. If you find yourself writing a paragraph with "but also" and "depends on" and "unless", use Opus — or run `/gsd:spec-phase` first to resolve the ambiguity before the model engages with it.

---

## How to override in Claude Code

**Session-level override:**
```
/model opus
```
This changes the model for the current session only. Useful when you know you are about to do high-ambiguity work and want Opus for the next few commands.

**Per-agent override in GSD config:** Open `.planning/config.json` and find the model profile section. Each agent type has a model field. Change the value to override the default. See the lab in this module.

---

## task-api: model assignment by GSD command

| GSD command | Recommended model | Reason |
|-------------|------------------|--------|
| `/gsd:new-project` | Opus | Synthesizes ambiguous project context into structured artifacts |
| `/gsd:spec-phase` | Opus | Ambiguity scoring and acceptance criteria require deep reasoning |
| `/gsd:discuss-phase` | Sonnet | Phase intent already clear; adaptive questioning at this depth |
| `/gsd:plan-phase` | Sonnet | Translating clear requirements into PLAN.md wave structure |
| `/gsd:execute-phase` | Sonnet | Executing defined tasks: writing handler.go, store.go, tests |
| `/gsd:verify-work` | Sonnet | Running checks against defined acceptance criteria |
| `/gsd:code-review` | Opus | Adversarial — finding issues the implementer missed |
| `/gsd:secure-phase` | Opus | Threat modeling, second-order security reasoning |
| `/gsd:milestone-summary` | Haiku or Sonnet | Summarizing completed artifacts; no reasoning required |
| `/gsd:audit-milestone` | Opus | Checking scope drift and missing acceptance criteria |

For task-api's three endpoints (GET /tasks, POST /tasks, DELETE /tasks/:id), all of them are simple enough that `/gsd:discuss-phase` and `/gsd:plan-phase` on Sonnet produce adequate plans. The phases where Opus matters are the ones involving security review and milestone audit — not the execution steps.

---

## Checklist

- [ ] I know the condition under which Sonnet is insufficient for planning (high ambiguity).
- [ ] I can state the two-sentence rule for model selection.
- [ ] I know the `/model` command for session-level override.
- [ ] I can look up where model assignments live in config.json.
- [ ] I understand why reviewer agents use Opus when executor agents use Sonnet.
