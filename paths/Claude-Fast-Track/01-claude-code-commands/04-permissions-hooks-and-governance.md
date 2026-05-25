# Permissions, hooks, and governance

## Permission model — what Claude can do without asking

By default, Claude Code prompts before running potentially destructive tools. The permission system lets you define what is always allowed (no prompt), what always requires confirmation (ask), and what is always blocked (deny).

**Deny beats allow.** If a path matches both an allow rule and a deny rule, deny wins.

Permissions are not context suggestions. They are enforced rules. CLAUDE.md saying "never read .env" is context — Claude may follow it or forget it. A deny permission on `.env` cannot be bypassed.

---

## Governance stack

```
Managed policy (org) ──► settings.json permissions ──► sandbox ──► hooks ──► human confirmation
```

Higher layers win on conflict. For individual developers, the relevant layers are settings.json permissions and hooks. For teams, managed policy may lock down what you can configure.

---

## settings.json — structure and examples

Permissions live in `.claude/settings.json` (project) or `~/.claude/settings.json` (user).

```json
{
  "permissions": {
    "allow": [
      "Bash(go test ./...)",
      "Bash(go build ./...)",
      "Bash(go vet ./...)",
      "Bash(git diff *)",
      "Bash(git status)",
      "Bash(git log *)"
    ],
    "ask": [
      "Bash(git commit *)",
      "Bash(git push *)",
      "Bash(go mod *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)",
      "Read(**/.env.*)",
      "Bash(rm -rf *)",
      "Bash(git push --force *)"
    ]
  },
  "defaultMode": "default"
}
```

### Rule syntax

| Tool | Pattern example | Matches |
|------|-----------------|---------|
| `Bash` | `Bash(go test ./...)` | Exact command prefix |
| `Bash` | `Bash(git diff *)` | git diff with any arguments |
| `Read` | `Read(./.env)` | Exact file path |
| `Read` | `Read(./secrets/**)` | Any file under ./secrets/ |
| `Edit` | `Edit(./src/**)` | Any file edit under ./src/ |
| `Write` | `Write(./generated/**)` | Any write under ./generated/ |

**`*` matches within a path segment. `**` matches across path segments.**

---

## Project vs user-level permissions

| Level | File | Scope | Committed? |
|-------|------|-------|------------|
| Project | `.claude/settings.json` | This repo only | Yes — shared with team |
| User | `~/.claude/settings.json` | All repos on your machine | No — personal only |

Project-level settings define what any developer who clones the repo can do with Claude Code. User-level settings add personal preferences on top.

**Principle:** put safety rules (deny .env, deny --force push) in project settings so the whole team benefits. Put personal workflow preferences (allow specific test commands) in user settings.

---

## Hooks — enforcement at lifecycle events

Hooks are scripts or commands Claude Code runs at specific lifecycle events. They are configured in `settings.json` under `"hooks"`.

### Hook events

| Event | When it fires | Typical use |
|-------|---------------|-------------|
| `PreToolUse` | Before Claude runs any tool | Block dangerous commands, validate preconditions |
| `PostToolUse` | After a tool completes successfully | Audit log, update state files, notify |
| `PostToolUseFailure` | After a tool fails | Alert, capture error context |
| `InstructionsLoaded` | When CLAUDE.md/rules are loaded (async) | Observe what memory loaded; debug |
| `PreCompact` | Before context compaction runs | Log what is about to be lost |
| `SessionStart` | When a new session begins | Inject session metadata, load dynamic context |

### Hook types

| Type | How it runs |
|------|-------------|
| `command` | Shell script or command; receives event JSON on stdin |
| `prompt` | Prompt injected into Claude's context |
| `http` | HTTP request to a webhook endpoint |
| `mcp_tool` | Call an MCP tool |

---

## Hooks configuration — full example

`.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-bash.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-edit-audit.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/pre-bash.sh` — minimal audit hook:

```bash
#!/usr/bin/env bash
# Receives PreToolUse event JSON on stdin.
# Log to a file for review; exit 0 to allow, exit 1 to block.
cat >> /tmp/claude-bash-audit.log
exit 0
```

`.claude/hooks/post-edit-audit.sh` — log file edits:

```bash
#!/usr/bin/env bash
# Receives PostToolUse event JSON on stdin.
# Extract the file path from JSON and log it.
python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('path','unknown'))" >> /tmp/claude-edits.log 2>/dev/null
exit 0
```

**Start with audit-only hooks (exit 0, log to file).** Only add blocking hooks (exit 1) after you have confirmed the audit logs look correct. A misconfigured blocking hook that fires on legitimate operations will interrupt all your work.

---

## Use cases for hooks

| Use case | Hook event | Action |
|----------|------------|--------|
| Block `git push --force` to main | `PreToolUse` on `Bash(git push *)` | Check args; exit 1 if `--force` |
| Audit all file edits | `PostToolUse` on `Edit\|Write` | Append to audit log |
| Update STATE.md after phase tasks | `PostToolUse` on `Edit` | Script that updates last-modified timestamp |
| Run linter after every Go file edit | `PostToolUse` on `Edit(*.go)` | Run `go vet` on changed file |
| Inject dynamic context at session start | `SessionStart` | Write current git branch and open issues to a temp file |
| Alert when Claude hits an error | `PostToolUseFailure` | Send notification to Slack webhook |

---

## Dangerous operations — what requires explicit confirmation

By default, Claude Code will prompt before:
- File deletion
- Git operations that affect remote state (push, force-push)
- Commands that cannot be undone (database drops, infrastructure changes)
- Network operations that have side effects

Do not put these in your allow list unless you understand the consequence. "Allow `Bash(terraform apply *)`" means Claude can apply infrastructure changes without asking.

**The measure-twice principle:** for any operation you cannot undo in under 5 minutes, keep it in `ask` even if it slows your workflow.

---

## Anti-patterns

| Anti-pattern | Risk | Fix |
|---|---|---|
| `--no-verify` to skip hooks | Hooks exist for safety; bypassing silently creates compliance gaps | Fix the root cause the hook catches |
| CLAUDE.md instruction instead of deny permission | Instructions are context; Claude can forget or override | Use deny for hard constraints |
| Full allow list copied from a tutorial | Allows commands specific to a different project's risk profile | Build your allow list incrementally from actual friction |
| No hooks at all | No audit trail; no enforcement | Start with a PostToolUse audit hook on Edit/Write |
| Blocking hook before audit verification | Misconfigured block interrupts legitimate work | Audit first, block second |

---

## Checklist

- [ ] Secrets paths are in `deny` in project settings.json.
- [ ] Destructive Bash commands (force push, rm -rf) are in `deny` or `ask`.
- [ ] I have at least one audit hook running (PostToolUse logging edits).
- [ ] I understand that deny beats allow in permission rule resolution.
- [ ] I know the difference between project-level and user-level settings.
- [ ] I can view current hooks with `/hooks`.
- [ ] I understand that hooks receive event JSON on stdin.
- [ ] I have not bypassed hooks with `--no-verify` without understanding the consequence.
