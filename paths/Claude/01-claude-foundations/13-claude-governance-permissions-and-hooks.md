# Claude governance — permissions, sandbox, hooks, managed policy

**Goal:** enforce **who may do what** — tool permissions, sandbox boundaries, hooks, and org **managed settings** — so Claude Code is safe on real repos.

**Docs:** [Permissions](https://code.claude.com/docs/en/permissions) · [Sandboxing](https://code.claude.com/docs/en/sandboxing) · [Hooks](https://code.claude.com/docs/en/hooks)

**Setup map:** `03-workspace-configuration.md`. **Approval workflows (process):** `24-approval-workflow/`.

Numerical prefixes = concept order only.

---

## Governance stack (layers)

```
Managed policy (org) ──► settings.json permissions ──► sandbox ──► hooks ──► human prompts
```

Higher layers win on conflict. **Permissions** are the daily knob; **managed** is enterprise lockdown.

---

## Permission rules

Stored in `settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(npm test)", "Bash(npm run lint)"],
    "ask": ["Bash(git push *)", "Bash(docker compose up *)"],
    "deny": ["Read(./.env)", "Read(./secrets/**)", "WebFetch"]
  }
}
```

**Interactive UI:** `/permissions` (alias `/allowed-tools`).

### Rule syntax (patterns)

| Tool | Example pattern |
|------|-----------------|
| Bash | `Bash(git diff *)` |
| Read | `Read(./src/**)` |
| Edit | `Edit(./src/**)` |
| MCP | Tool-specific — see permissions docs |
| Agent | Control subtext subagents may spawn |

**Deny beats allow.** Use **deny** for secrets and irreversible ops.

**Auto mode:** classifier + prose rules in `autoMode` setting — tune with `/fewer-permission-prompts` skill.

---

## Permission modes

| Mode | Risk |
|------|------|
| `default` | Baseline prompts |
| `acceptEdits` | Faster editing |
| `plan` | Design-only phase |
| `auto` | Rule-driven autonomy |
| `bypassPermissions` | **Highest** — often disabled by org |

Set `defaultMode` in settings; cycle in UI with Shift+Tab where available.

Org may set **`disableBypassPermissionsMode`**, **`allowManagedPermissionRulesOnly`**.

---

## Sandbox

**`/sandbox`** toggles sandbox mode (platform support required).

Sandbox settings (merged across scopes):

| Key | Purpose |
|-----|---------|
| `sandbox.filesystem.allowWrite` | Extra write paths |
| `sandbox.filesystem.denyWrite` | Block writes |
| `sandbox.filesystem.denyRead` | Block reads |

Align sandbox paths with **permission Read/Edit** rules — arrays merge, not replace.

---

## Hooks — enforcement at lifecycle events

Configure in **`settings.json`** → `"hooks"`.

| Event | Typical use |
|-------|-------------|
| `PreToolUse` | Block `terraform destroy`, require pattern |
| `PostToolUse` | Audit log |
| `PostToolUseFailure` | Alert |
| `InstructionsLoaded` | Observe CLAUDE.md/rules load (async, no block) |
| `PreCompact` | Log what context will be lost |
| `SessionStart` | Inject session metadata |

Hook types: **command** (shell), **prompt**, **agent** (experimental), **http**, **mcp_tool**.

**View:** `/hooks`.

**Org:** `allowManagedHooksOnly`, `disableAllHooks` — managed settings.

Skills and agents may define **scoped hooks** in frontmatter while active.

### Minimal audit hook lab

`.claude/hooks/audit-pretool.sh`:

```bash
#!/usr/bin/env bash
# Log PreToolUse JSON to stderr for inspection
cat >&2
exit 0
```

Wire in `.claude/settings.json` with matcher for `Edit|Write|Bash`.

Start **audit-only** before **deny** hooks unless fail-closed is required.

---

## Managed / enterprise governance

| Knob | Effect |
|------|--------|
| `allowedMcpServers` | MCP allowlist |
| `allowManagedPermissionRulesOnly` | Only org defines allow/ask/deny |
| `disableSkillShellExecution` | Block `!` shell in user/project skills |
| `skillOverrides` | Hide skills centrally |
| `claudeMd` in managed settings | Inject org CLAUDE content |

Document your org’s managed file location with internal IT — paths differ by OS.

---

## MCP governance

| Risk | Mitigation |
|------|------------|
| Over-broad filesystem MCP | Scope paths |
| Prod DB write | Read-only role |
| Untrusted project `.mcp.json` | Review before trust dialog |
| Prompt injection via tool output | Treat as hostile — `22-ai-security-engineering/` |

**`/mcp`** for connection management; **permission rules** for tool classes.

---

## Governance vs memory

| Need | Use |
|------|-----|
| “Never read `.env`” | **deny** permission |
| “Prefer 2-space indent” | CLAUDE.md |
| “Run formatter after every edit” | **PostToolUse** hook |
| “Block push to main” | **PreToolUse** on Bash |

Do not rely on CLAUDE.md alone for **hard safety** — permissions and hooks enforce.

---

## Lab — ALLOW / ASK / DENY matrix

Produce a personal or team matrix:

| Action class | allow | ask | deny |
|--------------|-------|-----|------|
| Read src | ✓ | | |
| Read secrets | | | ✓ |
| git commit | | ✓ | |
| git push | | ✓ | |
| npm test | ✓ | | |
| terraform apply | | | ✓ |

Implement top 5 rows in `.claude/settings.json`. Run **`/doctor`**. Test one denied Read.

Notebook output feeds **`14-claude-sandbox-safe-execution/`** integration lab.

---

## Checklist

- [ ] Secrets paths in **deny**.  
- [ ] Destructive Bash in **ask** or **deny**.  
- [ ] `/permissions` matches committed settings intent.  
- [ ] Hooks documented if used for compliance.  
- [ ] Managed policy acknowledged if on corporate machine.  
