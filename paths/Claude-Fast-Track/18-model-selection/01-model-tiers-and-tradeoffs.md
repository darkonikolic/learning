# Model tiers and tradeoffs

Claude models are not interchangeable. Picking the wrong model for a task either wastes money (using Opus for a classification task) or produces lower-quality output (using Haiku for complex architectural planning). Understanding the tiers and when each applies is a practical skill, not trivia.

---

## The three tiers

| Tier | Current model ID | Character |
|------|-----------------|-----------|
| Opus | claude-opus-4-7 | Most capable. Handles ambiguity, multi-step reasoning, complex tradeoffs. Slowest, most expensive. |
| Sonnet | claude-sonnet-4-6 | Balanced. Standard code generation, plan execution, typical structured workflow. Default for most work. |
| Haiku | claude-haiku-4-5 | Fastest, cheapest. Narrow tasks: classification, summarization, short lookups. Limited reasoning depth. |

Model IDs change as new versions are released. The tier names (Opus, Sonnet, Haiku) remain stable — the number suffix increments. When in doubt, check the Anthropic model page for the current IDs. What does not change is the tier hierarchy: Opus is always the most capable, Haiku is always the fastest.

---

## What "capable" means in practice

**Opus** handles tasks where the inputs are ambiguous, the requirements span multiple concerns, or the model must hold a large context in mind while making consistent decisions. Writing a SPEC for a complex feature, planning a multi-phase migration, or performing an adversarial security review are examples where Opus's deeper reasoning makes a measurable difference.

**Sonnet** handles tasks where the requirements are clear and the work is execution. Writing a handler function from a SPEC, generating a test suite from an acceptance criteria list, refactoring a module to a defined interface — these are tasks where Sonnet's output quality is sufficient and its speed and cost are meaningfully better than Opus.

**Haiku** handles tasks where the input is well-defined and the output is narrow. "Classify this log line as error, warning, or info" — Haiku. "Summarize this 500-line file in three sentences" — Haiku. "Should I use SQLite or PostgreSQL for this use case?" — not Haiku.

---

## Model assignment by agent type

Different agents benefit from different model tiers based on what they do:

- **Research agents** (plan-phase with research mode, spec writing) — use Opus because they synthesize ambiguous inputs
- **Executor agents** (execute-phase task execution, code writing) — use Sonnet because they implement clear specifications
- **Reviewer agents** (code-review, security review) — use Opus for adversarial quality
- **Summary/classification agents** (milestone summaries, status checks) — can use Haiku

You can configure model assignments per agent type in `.planning/config.json` — see the lab in this module.

---

## Cost and quality order of magnitude

These are rough order-of-magnitude comparisons, not exact prices. Prices change; the relative ratios are stable.

| Tier | Relative cost per token | Relative latency |
|------|------------------------|-----------------|
| Opus | ~5–10x Sonnet | ~2–3x slower than Sonnet |
| Sonnet | baseline | baseline |
| Haiku | ~0.1–0.2x Sonnet | ~3–5x faster than Sonnet |

For a typical execute-phase run on task-api (5 tasks, moderate code), the cost difference between running all tasks on Opus vs all on Sonnet is significant over many phases. Over a 20-phase project, using Opus everywhere when Sonnet would suffice accumulates into a meaningful cost difference.

---

## Extended thinking

Extended thinking is an Opus capability where the model reasons through a problem before producing its final response. You see the reasoning trace in the output.

When it helps: complex architectural decisions, spec ambiguity resolution, security threat modeling where the model must consider multiple attack vectors before responding. The reasoning trace also gives you visibility into how the model reached its conclusion — useful for auditing high-stakes decisions.

When it does not help: simple code generation, standard CRUD implementation, file formatting tasks. Extended thinking adds latency and cost with no quality benefit when the task does not require multi-step reasoning.

Extended thinking activates based on the model profile assignment. If you are using Opus for a task and want the reasoning trace visible, that is the default behavior.

---

## Checklist

- [ ] I can name the three model tiers and their current model IDs.
- [ ] I understand what "capable" means in terms of task type, not just quality rating.
- [ ] I know which agent types benefit from Opus and which are adequate with Sonnet.
- [ ] I can describe when extended thinking helps vs when it adds cost without benefit.
- [ ] I understand that model IDs change (version numbers) but tier names remain stable.
