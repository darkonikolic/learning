# Session commands — Claude Code slash reference

**Goal:** know **which `/` command to use when**, what it changes in session state, and how commands relate to **plan mode**, **context**, **MCP**, and **agents**.

**Product:** [Claude Code](https://code.claude.com/docs/en/overview) CLI only. Type `/` in a session to see commands available in **your** install — the table below is a study map, not a frozen API.

**Verify:** run **`/help`** after every `npx get-shit-done-cc@latest` or Claude Code upgrade. Bundled skills and command availability vary by version and plan.

Numerical prefixes = concept order only.

---

## How commands work

- Commands are recognized **only at the start of a message**; text after the command name becomes arguments.  
- **Built-in commands** — fixed CLI behavior (`/compact`, `/clear`, `/mcp`).  
- **Bundled skills** — prompt-based workflows Claude orchestrates (`/code-review`, `/debug`, `/batch`).  
- **Your skills** — same mechanism as bundled skills; directory name becomes `/skill-name`.  
- **MCP prompts** — dynamic `/mcp__<server>__<prompt>` from connected servers.

Deep authoring: `10-claude-skills-and-commands-authoring.md`.

---

## Commands across a typical workflow

Official grouping from Claude Code docs — memorize **phases**, not every row at once.

### First session in a repo

| Command | Why |
|---------|-----|
| `/init` | Generate starter `CLAUDE.md` (use `CLAUDE_CODE_NEW_INIT=1` for interactive skills/hooks/memory setup) |
| `/memory` | Edit memory files; toggle auto-memory |
| `/mcp` | Connect MCP servers, OAuth |
| `/agents` | Manage subagent definitions |
| `/permissions` | Set allow / ask / deny tool rules |

### During a task

| Command | Why |
|---------|-----|
| `/plan [description]` | Enter **plan mode** before large changes |
| `/model`, `/effort` | Control model and reasoning spend |
| `/context [all]` | See where the context window goes |
| `/compact [instructions]` | Summarize scrollback to free space |
| `/btw <question>` | Side question without bloating main thread |

### Parallel and background work

| Command | Why |
|---------|-----|
| `/agents` | Subagent manager |
| `/tasks` | Background tasks in session |
| `/background` (`/bg`) | Detach session; terminal free |
| `/batch` | Large change → parallel worktrees + subagents |

### Before you ship

| Command | Why |
|---------|-----|
| `/diff` | Interactive diff viewer |
| `/code-review` | Correctness pass on current diff |
| `/review`, `/security-review` | Deeper read-only review |

### Between sessions

| Command | Why |
|---------|-----|
| `/clear [name]` | New task, empty context (old chat kept in `/resume`) |
| `/resume`, `/branch` | Return or fork conversation |
| `/teleport`, `/remote-control` | Continue session across devices |

### When something breaks

| Command | Why |
|---------|-----|
| `/rewind` | Roll back code and/or conversation |
| `/doctor`, `/debug` | Install and runtime diagnosis |
| `/feedback` | Report bug with session context |

---

## Core commands — study set

Learn these first; expand via `/help` when needed.

| Command | Effect on session |
|---------|-------------------|
| `/help` | Full command list for your build |
| `/config` (`/settings`) | Settings UI — theme, model, defaults |
| `/plan` | Plan mode — design before edits |
| `/permissions` | Tool allow / ask / deny rules |
| `/context` | Context window visualization |
| `/compact` | Summarize history; **rules/memory survive per docs — verify** |
| `/clear` | Empty context; use when switching problems |
| `/memory` | CLAUDE.md + auto-memory management |
| `/mcp` | MCP server connections |
| `/agents` | Subagent configs |
| `/skills` | List skills; hide/show via Space |
| `/hooks` | View hook configurations |
| `/init` | Bootstrap project memory |
| `/add-dir <path>` | Extra working directory (file access only — most `.claude/` config not loaded from add-dir) |
| `/sandbox` | Toggle sandbox mode (platform-dependent) |
| `/rewind` | Checkpoint restore |

---

## Permission modes (not slash-only — also settings + Shift+Tab)

Configured in `.claude/settings.json` (`defaultMode`) or cycled in session:

| Mode | Behavior |
|------|----------|
| `default` | Prompt before risky tools |
| `acceptEdits` | Auto-accept file edits |
| `plan` | Plan-first |
| `auto` | Classifier allows/denies per rules |
| `dontAsk` | Fewer prompts (still not full bypass) |
| `bypassPermissions` | Dangerous — org policy may disable |

Use **`/permissions`** and **`/fewer-permission-prompts`** skill to tune without hand-editing JSON first.

Details: `13-claude-governance-permissions-and-hooks.md`.

---

## Context commands — critical distinction

| Command | Context | Conversation history |
|---------|---------|----------------------|
| `/compact` | Summarized | Continues same thread |
| `/clear` | Empty | New thread; old in `/resume` |
| `/branch` | Fork at point | Parallel branch |

**Before `/compact` on multi-step work:** ensure **plan lives on disk** (`04-plan-to-execution-workflow.md`). Compaction drops detail from scrollback.

**`/context`** shows CLAUDE.md, rules, skills, MCP tools consuming space — use it when responses feel “forgetful.”

---

## Custom and GSD commands

| Source | Example | Notes |
|--------|---------|-------|
| Project skill | `/deploy` from `.claude/skills/deploy/SKILL.md` | Same as legacy `.claude/commands/deploy.md` |
| Personal skill | `~/.claude/skills/...` | All projects |
| GSD plugin | `/gsd:plan-phase 1` | `15-gsd-commands.md` |
| MCP server | `/mcp__github__...` | Server-specific |

---

## Lab — command literacy sprint

On a repo with a small uncommitted change:

| Step | Command | Journal |
|------|---------|---------|
| 1 | `/context` | Top 3 context consumers |
| 2 | `/plan fix …` | Plan output shape; approve or edit |
| 3 | Implement one plan step in normal mode | Tools prompted? |
| 4 | `/diff` | Matches expectation? |
| 5 | `/compact summarize plan decisions only` | What still remembered vs lost |
| 6 | `/memory` | One line added to CLAUDE.md from lesson |

**Deliverable:** table — *command → state change → repeat?*

---

## Checklist

- [ ] I ran **`/help`** on my installed version this month.  
- [ ] I know **`/compact` vs `/clear`** and when plan must be on disk.  
- [ ] I used **`/context`** at least once to debug bloat.  
- [ ] I can reach **`/mcp`**, **`/agents`**, **`/permissions`** without guessing.  
