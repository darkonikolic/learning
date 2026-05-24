# Workspace configuration — Claude Code setup map

**Goal:** configure a project for Claude Code from zero — **settings**, **MCP**, **hooks**, **plugins** — and know **which file owns what** before diving into rules, skills, agents, and memory units (`09`–`13`).

**Docs:** [Settings](https://code.claude.com/docs/en/settings) · [Memory](https://code.claude.com/docs/en/memory) · [MCP](https://code.claude.com/docs/en/mcp) · [Hooks](https://code.claude.com/docs/en/hooks)

Numerical prefixes = concept order only.

---

## Configuration map

| Artefact | User | Project | Local / personal project |
|----------|------|---------|---------------------------|
| **Settings** | `~/.claude/settings.json` | `.claude/settings.json` | `.claude/settings.local.json` (gitignored) |
| **CLAUDE.md** | `~/.claude/CLAUDE.md` | `./CLAUDE.md` or `./.claude/CLAUDE.md` | `./CLAUDE.local.md` |
| **Rules** | — | `.claude/rules/*.md` | — |
| **Skills** | `~/.claude/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` | — |
| **Custom commands (legacy)** | `~/.claude/commands/` | `.claude/commands/` | Merged into skills |
| **Subagents** | `~/.claude/agents/` | `.claude/agents/` | — |
| **MCP servers** | `~/.claude.json` (user scope) | `.mcp.json` | Per-project in `~/.claude.json` |
| **Hooks** | In `settings.json` → `hooks` | Same | Same |
| **Plugins** | Settings + marketplace | `.claude/settings.json` | `.claude/settings.local.json` |
| **Managed policy** | Org admin paths | Overrides user/project | Compliance |

**Precedence:** managed > command-line flags > local > project > user (arrays often **merge**, not replace — see settings docs).

**Other state:** `~/.claude.json` holds OAuth, MCP user/local entries, per-project trust, caches.

---

## Settings.json — first project skeleton

Commit `.claude/settings.json` for team-shared policy:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)",
      "Read(./src/**)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)",
      "WebFetch"
    ]
  },
  "defaultMode": "default"
}
```

Use **`/permissions`** interactively before hand-authoring every rule.

Personal overrides → `.claude/settings.local.json` (never commit secrets).

Deep dive: `13-claude-governance-permissions-and-hooks.md`.

---

## Bootstrap a new repo — practical sequence

| Step | Action |
|------|--------|
| 1 | `claude` in repo root |
| 2 | `/init` (optionally `CLAUDE_CODE_NEW_INIT=1` for full artifact proposal) |
| 3 | `/permissions` — deny secrets paths, allow test/lint commands |
| 4 | `/mcp` — add servers the team needs (scoped credentials) |
| 5 | `/agents` — add subagents if you use role splits |
| 6 | Commit `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`, `.claude/rules/` as appropriate |
| 7 | Add `CLAUDE.local.md` to `.gitignore` for personal URLs / keys hints |

---

## MCP — project `.mcp.json`

Project-scoped servers live in **`.mcp.json`** (shareable). User/global entries in **`~/.claude.json`**.

| Step | Action |
|------|--------|
| 1 | Define server in `.mcp.json` per [MCP docs](https://code.claude.com/docs/en/mcp) |
| 2 | `/mcp` — authenticate (OAuth where required) |
| 3 | Trust dialog on first use in repo — **review project skills and MCP before accepting** |
| 4 | Smoke test: one prompt that requires a tool only that server exposes |

**Governance knobs:** `allowedMcpServers`, `enabledMcpjsonServers`, `allowAllProjectMcpServers` in managed or project settings — see `13`.

Orchestration mindset (not setup): `15-mcp-systems/`.

---

## Hooks — where they live

Hooks are configured inside **`settings.json`** under `"hooks"`, not a separate hooks-only file (unless using plugin `hooks/hooks.json`).

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": ".claude/hooks/audit-bash.sh" }]
      }
    ]
  }
}
```

View active config: **`/hooks`**.  
Guide: [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide).  
Detail: `13-claude-governance-permissions-and-hooks.md`.

---

## Plugins and GSD

| Extension | Config surface |
|-----------|----------------|
| **Plugins** | `/plugin` — skills, agents, hooks bundled |
| **GSD** | `.planning/config.json` + `/gsd:config` | `15-gsd-configuration.md` |

Keep **Claude Code project policy** in `.claude/` and **GSD phase state** in `.planning/` — cross-reference, do not duplicate REQUIREMENTS into CLAUDE.md walls.

---

## `.claudeignore`

Exclude paths from discovery (similar in purpose to ignore files for agent indexing). Use for artefacts, vendor trees, and local secrets directories.

---

## Configuration lab — minimum viable Claude Code repo

| # | Deliverable | Pass |
|---|-------------|------|
| 1 | `CLAUDE.md` with build/test commands | `/doctor` clean |
| 2 | `.claude/settings.json` with deny on `.env` | Agent blocked from reading `.env` |
| 3 | One `.claude/rules/` path-scoped rule | Loads when editing matched files |
| 4 | One project skill `/summarize-changes` or team equivalent | `/skills` lists it |
| 5 | One MCP server OR documented “none needed” | `/mcp` shows intent |
| 6 | Optional hook — audit-only `PreToolUse` | `/hooks` shows entry |

---

## Where to go deeper

| Topic | Unit |
|-------|------|
| Rules authoring | `09-claude-rules-authoring.md` |
| Skills & `/commands` | `10-claude-skills-and-commands-authoring.md` |
| Subagents | `11-claude-agents-and-subagents.md` |
| CLAUDE.md & auto memory | `12-claude-memory-and-persistence.md` |
| Permissions, sandbox, managed policy | `13-claude-governance-permissions-and-hooks.md` |
| GSD commands | `15-gsd-commands.md` |
| GSD `.planning/` config | `16-gsd-configuration.md` |
| GSD plan-to-ship | `17-gsd-plan-to-ship-workflow.md` |
| SPEC before code (foundations) | `05-specification-before-implementation.md` |

---

## Checklist

- [ ] I can draw the **config map** without looking.  
- [ ] Team policy is in **git**; secrets and personal prefs are **not**.  
- [ ] I ran **`/init`** or consciously skipped with written reason.  
- [ ] MCP scope is minimal; trust dialog understood before accept.  
