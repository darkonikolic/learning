# Decision log

Append-only record of system design decisions and why. Newest on top.

## 2026-05-29 — project-A mandatory build workflow (with tooling step)

- Added `project-a-workflow.mdc` (glob-scoped `paths/project-A/**`, not alwaysApply): every module's work has two outputs — the DevOps result AND set-up/updated agents/rules/skills.
- Loop: 0) Tooling setup/update → 1) Plan (Plan mode) → 2) Discuss + adapt → 3) Execute → 4) Validate → 5) Capture (fold learnings back into config).
- **Anti-sprawl guard** built in: do not create a rule/agent/skill per module by reflex; use `/system-maintainer` + `process-feedback` to decide; need is data, not reflex.
- Chose a scoped rule over editing 230 module files (avoids duplication rot) and over a new standalone system (user wanted it baked into every module's work, not new).

## 2026-05-29 — project-A review fixes + language policy

- **Language:** `project-A` stays Serbian (ekavica) by user decision; governance rule updated with an exception. No auto-translation/dialect conversion of existing traces — ask first.
- **Truthfulness:** removed the stale module list in `00-orientation/01-sta-ces-izgraditi.md` (it used old numbering `06b/07-terraform-aws/...` up to 20); kept the accurate `00`–`28` list and merged in the "ručno → Terraform → pipeline" principle.
- **Helm gap:** replaced empty `04-helm/templates` and `04-helm/values` dirs with a real reference chart `04-helm/helloworld/` (Chart.yaml, base + per-env values, templates with commented explanations), matching `02-chart-struktura.md`.
- **Layout note:** runnable reference assets (like the Helm chart dir) are allowed in `project-A` alongside `NN-*.md` and are exempt from `NN-*` numbering — recorded in governance rule.

## 2026-05-29 — No personal data (user directive)

- User does not want **any** stored personal data: no learner profile, no competency records, no decision journal.
- Deleted `memory/learner_profile.md`, `memory/competency.md`, `memory/decision_journal.md`.
- `track-competency`, `map-to-known`, `check-prerequisites` now work **session-only**: ask in-session, assess, discard — persist nothing personal.
- `learning-memory` rule: only system working-style/design memory is stored (`user_preferences`, `common_corrections`, `anti_patterns`, `decision_log`); no personal learner data.

## 2026-05-29 — Material-quality modules added, folded not proliferated

- Added skills `check-prerequisites`, `map-to-known` (transfer learning), `track-competency` (evidence-based, with 7/30/90 decay).
- Added memory `competency.md`, `decision_journal.md` (learner focus, ≠ system `decision_log`), `learner_profile.md`.
- **Folded into existing always-apply rules instead of new files** (already 9 always-apply): confidence levels + claim≠competency + red flags → `reality-guard`; anti-tutorial trap → `practice-first`; industry-usage tag + cost + time-to-X (chat-only) → `real-world-focus`; prerequisite + transfer hooks → `learning-core`.
- **Honored governance:** knowledge-decay schedules and time-to-goal stay in chat/memory, never written as pacing into trace `.md`.
- **Rejected** a separate "Prerequisite Analyzer" agent and standalone Time/Cost rules: folded to avoid agent/rule sprawl.
- `learner_profile.md` background ("14+ yrs Symfony") seeded as **unconfirmed** — must be confirmed by the user (`reality-guard`: no fabricated certainty).

## 2026-05-29 — Feedback layer (Layer 4) added, selectively

- Added `reality-guard` rule, forbidden-phrase list into `no-bullshit`, learning-path rule into `real-world-focus`.
- Added `.cursor/memory/` + `learning-memory` rule + `/system-maintainer` + `process-feedback` skill.
- **Rejected** the `system/{agents,skills,rules,memory,feedback}` reorg: Cursor loads `.cursor/{rules,commands,skills}` natively; a `system/` folder would not load and would break the working setup. Memory lives under `.cursor/memory/` instead.
- **Rejected** a separate "Practicality Guard" rule: already covered by `learning-core` + `explain-concept`; avoided duplication.
- Dropped a separate `learned_rules.md`: confirmed rules graduate into real `.mdc` files; `common_corrections.md` is the staging area.

## 2026-05-29 — Initial 3-layer system

- Agents represented as slash commands (`.cursor/commands/`) because Cursor has no stable committed "custom agent" file primitive.
- 6 global always-apply rules + 1 system map; 11 agent commands; 10 action skills.
- `plan-ucenja-ciljevi-i-rad.mdc` retains precedence over agents/skills.
