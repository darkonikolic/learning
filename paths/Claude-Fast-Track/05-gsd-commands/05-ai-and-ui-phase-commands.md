# AI and UI phase commands

Specialized commands that produce design contracts for phases that involve LLM integration or frontend implementation. Both commands run before execute-phase — they produce a spec artifact that shapes the plan, not code.

---

## `/gsd:ai-integration-phase <N>`

### Purpose

For phases that call an LLM API, build agent pipelines, use embeddings, or implement any behavior where a neural model produces output. This command produces an AI-SPEC.md design contract before any code is written.

### What it produces

`AI-SPEC.md` under the phase folder. Contents:

| Section | Holds |
|---------|-------|
| Framework selection | Which LLM, which SDK, reasoning |
| Prompt architecture | System prompt structure, user prompt schema, few-shot examples |
| Evaluation strategy | What dimensions to measure, at what point in the pipeline |
| Guardrails | Input validation, output validation, refusal handling |
| Monitoring | What to log, what to alert on, latency SLOs |
| Cost model | Estimated token spend per operation |
| Fallback behavior | What happens when the model call fails or times out |

### Spawned agents

The command runs multiple sub-agents in parallel:
- **Framework selector:** Evaluates LLM options against requirements (cost, latency, capability, compliance).
- **AI researcher:** Investigates domain-specific prompting techniques and known failure modes.
- **Domain researcher:** Gathers context about the specific task the LLM is performing.
- **Eval planner:** Designs the evaluation suite before implementation begins.

### When to run

Any phase where Claude (or another LLM) is a runtime component — not just a coding tool. If your code calls `client.messages.create(...)` at runtime, run this command.

**Not needed for:** phases where you use Claude Code as a development assistant but the deployed code has no LLM calls.

### How it integrates with the core loop

```
discuss-phase N  -->  /gsd:ai-integration-phase N  -->  plan-phase N  -->  execute-phase N
                               |
                           AI-SPEC.md
                       (consumed by planner)
```

Run ai-integration-phase after discuss, before plan. The planner reads AI-SPEC.md and structures tasks around the evaluation strategy and framework selection.

### Task-api relevance

Not applicable to the task-api toy project — it is a standard Go HTTP API with no LLM calls. If you extended it to auto-categorize tasks using an LLM, this command would be required before planning that phase.

---

## `/gsd:ui-phase <N>`

### Purpose

For phases that implement frontend UI. Produces a UI-SPEC.md design contract before any HTML, CSS, or component code is written.

### What it produces

`UI-SPEC.md` under the phase folder. Contents:

| Section | Holds |
|---------|-------|
| Layout specification | Grid, regions, responsive breakpoints |
| Component inventory | Each component, its states, its props |
| Interaction states | Hover, focus, active, disabled, loading, error |
| Typography system | Font scale, weight usage rules |
| Color system | Primary, secondary, semantic colors with hex values |
| Accessibility requirements | WCAG level, keyboard navigation, ARIA roles |
| Animation and transitions | What moves, duration, easing |

### When to run

Before implementing any frontend phase. The UI-SPEC.md becomes the source of truth for the implementation — executor agents build to it, and `/gsd:ui-review` audits against it.

### Relationship to `/gsd:ui-review`

| Command | When | Purpose |
|---------|------|---------|
| `/gsd:ui-phase N` | Before execute | Design contract |
| `/gsd:ui-review` | After execute | Audit against contract |

UI-phase is the spec. UI-review is the verification. Running ui-review without a ui-phase spec means reviewing against nothing — findings will be subjective.

### Task-api relevance

Not applicable. The toy project has no frontend. If you added a React task list UI, run ui-phase before implementing it.

---

## `/gsd:eval-review`

### Purpose

Retroactive audit of AI evaluation coverage after executing an AI integration phase.

### When to run

After executing an AI phase, before ship. Answers: "Did we actually implement the evaluation strategy in AI-SPEC.md, or did we just ship the happy path and assume it works?"

### What it produces

`EVAL-REVIEW.md` with a coverage table:

| Dimension | Coverage | Finding |
|-----------|---------|---------|
| Correctness (output accuracy) | COVERED / PARTIAL / MISSING | Details |
| Latency (p50/p95 within SLO) | COVERED / PARTIAL / MISSING | Details |
| Safety (refusal, injection) | COVERED / PARTIAL / MISSING | Details |
| Cost (token spend within budget) | COVERED / PARTIAL / MISSING | Details |
| Regression (golden set passing) | COVERED / PARTIAL / MISSING | Details |

Any MISSING finding blocks ship unless explicitly waived in STATE.md with justification.

---

## `/gsd:ui-review`

### Purpose

6-pillar visual audit of implemented frontend code. Retroactive — runs after execute, not before.

### 6 pillars

| Pillar | What it checks |
|--------|---------------|
| Layout | Grid alignment, region boundaries, overflow behavior |
| Typography | Font usage consistent with spec, size hierarchy |
| Color and contrast | Hex values match spec, WCAG contrast ratios met |
| Spacing | Margin/padding system consistency |
| Interaction states | Hover, focus, disabled implemented for every interactive element |
| Accessibility | Keyboard navigation, ARIA attributes, screen reader text |

### Output

`UI-REVIEW.md` with scored findings (PASS / WARN / FAIL) per pillar per component.

Any FAIL finding blocks ship unless waived.

---

## Sequence diagram: AI phase with full quality loop

```
discuss-phase N
      |
ai-integration-phase N   <-- produces AI-SPEC.md
      |
plan-phase N             <-- consumes AI-SPEC.md
      |
execute-phase N
      |
code-review              <-- general quality
      |
eval-review              <-- AI-specific coverage
      |
verify-work
      |
ship
```

Do not skip eval-review for AI phases. The core loop verify-work is conversational UAT — it checks behavior interactively. Eval-review checks that the evaluation infrastructure exists at all. These are different checks.

---

## Checklist

- [ ] I know ai-integration-phase runs after discuss and before plan (not before discuss).
- [ ] I know the four sub-agents that ai-integration-phase spawns.
- [ ] I understand the difference between ui-phase (spec) and ui-review (audit).
- [ ] I know what EVAL-REVIEW.md contains and what blocks ship.
- [ ] I know the 6 pillars of ui-review.
- [ ] I can explain why eval-review is needed in addition to verify-work for AI phases.
