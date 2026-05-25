# config.json and GSD toggles

GSD's runtime behaviour is controlled by `.planning/config.json`. This file governs which model agents use, how many run in parallel, whether quality gates run automatically, and whether GSD stops for human confirmation. Understanding config.json means knowing which knob to turn when GSD is too slow, too aggressive, or making wrong model choices.

---

## Location and creation

`.planning/config.json` is created by `/gsd:new-project` and updated by `/gsd:config` and `/gsd:settings` commands. Never edit it directly in production workflows — use the commands to avoid schema drift between GSD versions.

---

## Full annotated config.json example

```json
{
  "version": "2.0",
  "project": "task-api",

  "model_profile": {
    "profile": "balanced",
    "planner": "claude-opus-4-5",
    "executor": "claude-sonnet-4-5",
    "verifier": "claude-sonnet-4-5",
    "researcher": "claude-haiku-4-5",
    "reviewer": "claude-sonnet-4-5"
  },

  "workflow": {
    "mode": "interactive",
    "auto_approve_plans": false,
    "auto_approve_execute": false,
    "pause_between_waves": true,
    "require_spec_before_plan": false
  },

  "agents": {
    "parallel_executor_count": 3,
    "research_enabled": true,
    "verifier_enabled": true,
    "plan_check_enabled": true,
    "tdd_default": false
  },

  "git": {
    "branch_strategy": "phase-branch",
    "branch_template": "gsd/{phase-slug}",
    "auto_commit": false
  },

  "integrations": {
    "cross_ai_review": false,
    "external_review_cli": null
  }
}
```

---

## Key toggles explained

### model_profile

Controls which Claude model each agent role uses. Profiles are preset bundles; individual overrides are possible.

| Profile | Planner | Executor | Cost |
|---------|---------|---------|------|
| `quality` | opus | sonnet | High — use for production features |
| `balanced` | opus | sonnet (haiku research) | Medium — default for learning |
| `budget` | sonnet | haiku | Low — use for exploration, prototyping |

Match the profile to task criticality. A learning exercise on the task-api can use `budget`. A production payment service should use `quality` for plan phases at minimum.

The model profile in config.json affects **GSD-orchestrated agents only**. It is orthogonal to the model you select for your main Claude Code session with `/model`. Misalignment between the two wastes budget or degrades quality — check both when cost is unexpected.

### workflow.mode

| Value | Behaviour |
|-------|-----------|
| `interactive` | GSD pauses at each phase gate for your approval |
| `yolo` | GSD proceeds without pausing — dangerous on production repos |

`yolo` mode is appropriate only for isolated toy projects where any mistake is a learning opportunity. Never use it on a repo with live data, production branches, or shared team history. The time saved is not worth the risk of an execute-phase running on the wrong context.

### workflow.auto_approve_plans and auto_approve_execute

When `false` (default), GSD shows you the plan and waits for your `yes` before executing. When `true`, it proceeds immediately. Keep both `false` unless you are running a fully automated pipeline with verified test coverage gating every step.

### agents.parallel_executor_count

Controls how many executor agents run concurrently during `/gsd:execute-phase`. Default is 3. Raise to 5-6 on large phases with independent wave tasks to cut wall-clock time. Lower to 1 for debugging a failed execute — parallel agents produce interleaved output that is hard to read.

### agents.tdd_default

When `true`, `/gsd:plan-phase` always produces test tasks before implementation tasks. Equivalent to always passing `--tdd` to plan-phase. Enable this once your test workflow is established. On the task-api, enable it before Phase 02 (validation) to drive test-first patterns.

### agents.research_enabled

When `true`, `/gsd:plan-phase` spawns a research agent to survey prior art, risks, and alternatives before producing the PLAN.md. Adds latency but produces higher-quality plans. Disable for trivial phases (< 3 tasks) to save time and tokens.

### workflow.require_spec_before_plan

When `true`, `/gsd:plan-phase` refuses to run if no `SPEC.md` exists in the phase directory. Strong enforcement of spec-first discipline. Enable this after Module 07 of this course.

---

## Changing config with commands

| Command | What it changes |
|---------|----------------|
| `/gsd:config` | Common toggles interactively — mode, research, verifier, tdd |
| `/gsd:config --advanced` | Timeouts, branch templates, cross-AI execution |
| `/gsd:config --integrations` | API keys, external review CLIs |
| `/gsd:config --profile quality\|balanced\|budget` | Model profile shortcut |
| `/gsd:settings` | Full settings UI with descriptions |

### Example: switch to budget profile

```
/gsd:config --profile budget
```

GSD updates `config.json` and shows you the diff. Confirm, and the next plan-phase uses the budget model set.

---

## /gsd:surface — toggle which skills are active

`/gsd:surface` controls which GSD skills are surfaced in your Claude Code session. This is not about config.json — it is about which slash commands appear as available options.

```
/gsd:surface list              ← see what is currently active
/gsd:surface profile minimal   ← surface only core commands (progress, execute, resume)
/gsd:surface profile full      ← surface all skills
/gsd:surface disable graphify  ← hide a specific skill
```

Use `surface profile minimal` when you are deep in execution and do not want exploration commands cluttering the namespace. Use `full` during planning and review phases.

---

## Command flags vs config changes

Use flags for one-off overrides. Use config changes for persistent defaults.

| Scenario | Approach |
|---------|---------|
| One phase needs research, rest do not | `/gsd:plan-phase --research` flag |
| All phases from now on need research | Set `agents.research_enabled: true` in config |
| Single plan with TDD | `/gsd:plan-phase --tdd` flag |
| Project-wide TDD | Set `agents.tdd_default: true` in config |
| Debug a specific execute | Set `parallel_executor_count: 1` temporarily |
| Permanent parallel execution | Set it in config |

Flags override config for a single command run. They do not persist to config.json.

---

## Checklist

- [ ] I know the location of config.json and that I use commands, not hand-edits, to change it
- [ ] I know the three model profiles and when to use each
- [ ] I know that model_profile in config.json is separate from /model in Claude Code
- [ ] I know what yolo mode does and why it is dangerous
- [ ] I know what tdd_default does and when to enable it
- [ ] I know the difference between command flags (one-off) and config changes (persistent)
- [ ] I know what /gsd:surface does and the minimal vs full profiles
- [ ] I know how to use /gsd:config --profile to switch model profiles
