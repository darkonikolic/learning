# Human authority and override

`03-human-in-the-loop.md` covers approval gates and permission tiers. This file covers **when you stop Claude**, **when manual investigation wins**, and **trust calibration**.

---

## When to stop Claude

Stop autonomous work (no more execute, no more “just one more fix”) when:

| Trigger | Why |
|---------|-----|
| **Stop** confidence (`13-agent-reliability/01-when-agents-fail.md`) | Loop or SPEC ambiguity |
| **Irreversible** action next | push, deploy, migration, mass delete |
| **Two sources conflict** and SPEC does not resolve | Human picks ground truth |
| **Security surprise** | Unexpected credential, egress, or package |
| **You cannot state expected behavior** in one sentence | Frame failure |
| **Blast radius unclear** | Cannot name worst case (`09-sandbox-safe-execution/01-sandbox-thinking.md`) |

**Stop actions:** `/clear` or end session after writing `docs/state.md` and open decisions to a file.

---

## When to bypass AI

Bypass Claude for this task (you do it; Claude observes or waits):

| Situation | Reason |
|-----------|--------|
| **Production incident** | Time pressure; need tactile debugging |
| **Subtle race or perf** | May need profiler, debugger, load test |
| **Political / compliance call** | Model should not decide |
| **First read of alien module** | 15 min Read builds map cheaper than agent thrash |
| **Git surgery** | Rebase, conflict resolution you already understand |

You can still use Claude **after** you have a hypothesis: “here is stack trace; suggest one change in `store.go` only.”

---

## When manual investigation wins

| Signal | Manual step |
|--------|-------------|
| Flaky test | Run 20× locally; bisect |
| “Sometimes 404” | curl loop; log correlation |
| Wrong data shape | DB or in-memory inspect; not guess from handler |
| Cross-service bug | Trace IDs; logs — MCP may help, you verify |

Claude accelerates **known** search paths. It does not replace **ownership** of production truth.

---

## Human authority boundaries

| You always own | Claude may propose |
|--------------|-------------------|
| Merge / push | Commits locally (if allowed) |
| SPEC and product intent | Draft SPEC |
| Permission policy | Suggest settings |
| “Ship or not ship” | Test results |
| Exception to rules | Apply with documented exception (`16-rule-conflicts/`) |

**Turn instruction wins** over project rules for *this message* — but security-tier rules still block (see `16-rule-conflicts/01-conflict-resolution.md`).

---

## Uncertainty escalation

When Claude asks a clarifying question, treat it as **HITL done right** — not annoyance.

| Claude asks | You respond with |
|-------------|------------------|
| Two valid interpretations | Pick one; update SPEC if recurring |
| “Overwrite file?” | Yes/no + scope |
| “Add dependency?” | No — cite stdlib rule |

When Claude **does not** ask but should (silent assumption), that is **hallucinated assumption** — classify and repair (`13-agent-reliability/03-claude-failure-taxonomy.md`).

---

## Trust calibration

Trust is **per task class**, not per model brand.

| Task class | Starting trust | Earned by |
|------------|----------------|-----------|
| Read + summarize file | Medium | Spot-check lines |
| Single-file bounded edit | Medium | Diff + test |
| Multi-file feature | Low until plan approved | Wave verify |
| Security-sensitive | Low | Review + deny list |
| Refactor | Low | Template + incremental steps (`12-diff-refactor/`) |

**Do not** raise trust because output “looks professional.” Raise trust when **verification you ran** passes.

---

## Checklist

- [ ] I stop after Stop confidence or irreversible risk.
- [ ] I know three cases where I work without Claude first.
- [ ] I answer Claude’s clarifying questions with explicit decisions.
- [ ] I calibrate trust per task class, not per eloquence.
- [ ] I update `docs/state.md` when stopping mid-phase.
