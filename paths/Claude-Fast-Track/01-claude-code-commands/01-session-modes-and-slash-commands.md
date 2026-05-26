# Session modes and slash commands

## Claude Code is a CLI, not a chat

Claude Code is Anthropic's **coding agent** product ([claude.com](https://claude.com/) → Claude Code). It is not the same surface as browser chat or Cowork, though it shares models and account.

The distinction matters for how you work. In a chat interface, context accumulates passively and you navigate by scrolling. In Claude Code:

- Context is a finite resource you actively manage.
- Commands change session state — they are not just shortcuts for asking questions.
- Work products should land on disk, not in the chat thread.
- Sessions end. The next session starts cold.

Treat each session as a deployment unit: it starts with a purpose, runs tools, writes files, and ends with state committed to disk. The transcript is ephemeral.

---

## Session modes

| Mode | How to enter | Behavior |
|------|------|----------|
| Normal | Default | Claude executes tools after proposing |
| Plan mode | `/plan` or Shift+Tab | Claude proposes only — no tool execution until you approve |
| Auto | `defaultMode: auto` in settings | Classifier-driven; runs allowed tools without prompting |
| Accept-edits | Shift+Tab cycle | Auto-accepts file edits; still prompts for Bash |

**Rule of thumb — when to use /plan:**
Use `/plan` before any change that touches more than two files, involves a migration, restructures a package, or you are uncertain about scope. Use normal mode for single-file, clearly-scoped edits.

Never use normal mode for "implement the whole feature" — that skips the plan review step where you catch misunderstood requirements.

---

## Core slash commands

Run `/help` after every Claude Code upgrade. Commands vary by version.

### Navigation and context

| Command | Effect | When to use |
|---------|--------|-------------|
| `/help` | Full command list for current install | First thing in a new install |
| `/context` | Show context window usage by source | When responses feel forgetful or context is large |
| `/compact [instructions]` | Summarize scrollback; free context space | Before starting a new sub-task in a long session |
| `/clear [name]` | Empty context; start new thread | When switching to a different problem entirely |
| `/resume` | Return to a previous named session | Picking up yesterday's work |

### Planning and execution

| Command | Effect | When to use |
|---------|--------|-------------|
| `/plan [description]` | Enter plan mode; Claude proposes without executing | Before any multi-file change |
| `/diff` | Interactive diff viewer | Before committing or reviewing a change |
| `/rewind` | Roll back code and/or conversation to checkpoint | When Claude made a wrong turn |

### Review and quality

| Command | Effect | When to use |
|---------|--------|-------------|
| `/review` | Review current diff | Before merge on risky changes |
| `/code-review` | Correctness pass on current diff | Automated review before PR |
| `/security-review` | Security-focused review | Changes that touch auth, secrets, network |

### Configuration and setup

| Command | Effect | When to use |
|---------|--------|-------------|
| `/config` (alias `/settings`) | Settings UI — theme, model, defaults | Finding settings.json location |
| `/permissions` | Tool allow/ask/deny rules | Tuning what Claude can run without prompting |
| `/memory` | CLAUDE.md + auto-memory management | After run to add lessons |
| `/init` | Generate starter CLAUDE.md from repo analysis | First session on a new project |
| `/mcp` | MCP server connections | Adding new tool integrations |
| `/agents` | Subagent configs | Creating or managing specialized agents |
| `/hooks` | View hook configurations | Debugging hook behavior |

### Parallelism and background

| Command | Effect | When to use |
|---------|--------|-------------|
| `/batch` | Decompose large change into parallel worktrees + subagents | Large refactors across many files |
| `/tasks` | Background tasks in current session | Monitoring long-running subagents |
| `/background` (alias `/bg`) | Detach session; terminal free | When you need the terminal back |

### Diagnostics

| Command | Effect | When to use |
|---------|--------|-------------|
| `/doctor` | Install and runtime diagnosis | Setup failures or unexpected behavior |
| `/debug` | Runtime debug | Tool failures |
| `/cost` | Token usage for session | Budget tracking |

---

## Keyboard shortcuts reference

| Shortcut | Action |
|----------|--------|
| Shift+Tab | Cycle permission modes (default → plan → auto) |
| Ctrl+C | Interrupt current tool execution |
| Ctrl+R | Search command history |
| Up/Down | Navigate message history |
| Tab | Autocomplete command names |

Verify these in your install — shortcuts can vary by terminal and platform.

---

## /plan vs normal mode — the decision

**Use /plan when:**
- The task description contains "refactor", "migrate", "restructure", or "implement [feature]"
- More than two files will be created or modified
- You have not confirmed Claude's understanding of the requirement
- The change is irreversible without significant effort (DB migrations, large deletes)

**Use normal mode when:**
- Fixing a single identified bug in a known location
- Adding one function to an existing file you just read
- Running tests or inspecting output
- You approved a plan and are now executing a specific step from it

**Never do this:**
```
You: implement the complete task-api with all three endpoints and tests
Claude: [writes 15 files without asking a single question]
```

**Do this instead:**
```
You: /plan implement the three endpoints for the task-api based on docs/specs/ and docs/plans/
Claude: [proposes approach — you review and approve or correct]
You: proceed with task 1
```

---

## /compact — what it does and when to use it

`/compact` summarizes the chat scrollback into a compressed representation. It frees context space for new work.

**What survives compaction:** CLAUDE.md, rules files, active memory. Plans and decisions discussed only in chat do not survive fully.

**When to use it:**
- You are 60-70% through context window (check with `/context`)
- You are switching from exploration/discussion to execution
- You have been iterating in chat but the plan now lives in `docs/plans/<phase>-plan.md`

**Before running /compact on multi-step work:**
- Ensure the current plan is written to `docs/plans/<phase>-plan.md` on disk
- Ensure `docs/state.md` reflects current phase and last completed task
- Ensure any decisions made in chat are captured in a file

Running `/compact` without writing decisions to disk is how you lose irreplaceable context.

---

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Never using /plan | Scope surprises mid-execution | Use /plan for any multi-file change |
| /compact too late | Context window full; compaction loses important state | Compact at 60-70%, not 99% |
| Long exploration in chat | Decisions exist only in scrollback | Write decisions to files as you make them |
| Ignoring /context output | CLAUDE.md bloat goes unnoticed | Run /context weekly on active projects |
| Re-typing context every session | No CLAUDE.md | Run /init; maintain CLAUDE.md |

---

## Checklist

- [ ] I ran `/help` on my installed version and read the output.
- [ ] I understand the difference between `/compact` (summarize) and `/clear` (empty).
- [ ] I know when to use `/plan` vs normal mode.
- [ ] I have used `/context` at least once to see where context space is going.
- [ ] I understand that decisions discussed only in chat do not survive `/compact` reliably.
- [ ] I can reach `/permissions`, `/memory`, and `/hooks` without guessing.
- [ ] I know what `/rewind` does and when I would need it.
- [ ] I know that `/init` generates a starter CLAUDE.md from repo analysis.
