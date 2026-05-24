# Claude skills and custom commands — practical authoring

**Goal:** create **`SKILL.md`** workflows (and legacy **`.claude/commands/`** if needed) that you invoke with **`/name`** or Claude loads when relevant.

**Docs:** [Extend Claude with skills](https://code.claude.com/docs/en/skills) · [Commands reference](https://code.claude.com/docs/en/commands)

**Rules (always-on policy):** `09-claude-rules-authoring.md`. **Deep engineering:** `25-skills-and-rules-engineering/`.

Numerical prefixes = concept order only.

---

## Skills vs commands (merged model)

Custom commands were **merged into skills**:

| Legacy | Modern | Result |
|--------|--------|--------|
| `.claude/commands/deploy.md` | `.claude/skills/deploy/SKILL.md` | Both expose `/deploy` |
| Same name | Skill wins over command file | One behavior |

Prefer **skill directories** — room for supporting files and richer frontmatter.

---

## Where skills live

| Scope | Path |
|-------|------|
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` |
| Plugin | Plugin `skills/` tree |
| Enterprise | Managed settings |

**Precedence:** enterprise > personal > project. Plugin namespaced as `plugin:skill`.

**Live reload:** edits under skill dirs apply within session; new top-level skill roots may need restart.

**Discovery:** project skills load from cwd up to repo root; nested `.claude/skills/` load when working in subdirs (monorepos).

---

## SKILL.md anatomy

```markdown
---
name: summarize-changes
description: Summarizes uncommitted git changes and flags risks. Use when user asks what changed or wants a commit message.
disable-model-invocation: false
allowed-tools: Read, Bash
---

## Current diff

!`git diff HEAD`

## Instructions

Summarize in three bullets. List risks (missing tests, secrets, breaking API).
```

### Important frontmatter fields

| Field | Purpose |
|-------|---------|
| `description` | Auto-invocation trigger — write like docstring for when Claude should load skill |
| `disable-model-invocation: true` | **Manual only** — you must type `/name` |
| `allowed-tools` | Restrict tools while skill active (review before trusting project skills) |
| `hooks` | Skill-scoped lifecycle hooks |
| `context: fork` | Run skill in isolated subagent context (see skills docs) |

**Visibility override:** `/skills` → Space to hide; writes `skillOverrides` in `settings.local.json`.

---

## Dynamic context injection

Lines starting with **`!`**backticks** run shell before Claude sees the skill:

```markdown
!`git log -5 --oneline`
```

Use for live diffs, test output, version strings — keeps skill body small until invoked.

---

## Control who invokes

| Pattern | Setting |
|---------|---------|
| Claude auto-loads when relevant | `disable-model-invocation: false` (default) |
| You only — slash command | `disable-model-invocation: true` |
| Bundled-style always available | Ship as project skill with clear description |

---

## Bundled skills to know

Study via `/help` — common ones:

| Skill | Use |
|-------|-----|
| `/code-review` | Diff correctness |
| `/debug` | Session debug log analysis |
| `/batch` | Parallel large migrations |
| `/loop` | Repeated prompt on interval |
| `/run`, `/verify` | App running verification (2.1.145+) |
| `/fewer-permission-prompts` | Learn allow rules from transcripts |

Treat bundled skills as **reference implementations** for your own SKILL.md quality.

---

## Authoring procedure

1. **Name** the skill after the verb users will type (`/deploy`, `/incident-triage`).  
2. **Description** — include trigger phrases users actually say.  
3. **Inputs** — what must exist (branch clean, env var set).  
4. **Steps** — numbered; each step names tool class (Read, Bash, MCP).  
5. **Output** — exact artefact (markdown section, PR text, table).  
6. **Failure** — what to do if command fails.  
7. **Test** — invoke via `/name` and via natural language matching description.

---

## Lab — git summarize skill

| Step | Action |
|------|--------|
| 1 | Create `.claude/skills/summarize-changes/SKILL.md` from docs example |
| 2 | Make a small edit; run `/summarize-changes` |
| 3 | Ask “what did I change?” without slash — observe auto-load |
| 4 | Set `disable-model-invocation: true`; confirm only manual works |
| 5 | Add `allowed-tools: Bash, Read` — verify restricted behavior |

---

## Security note

Project skills can include **`allowed-tools`** that broaden access after workspace trust. **Review `.claude/skills/` in PRs** like application code.

Org may set **`disableSkillShellExecution`** — inline `!` shell in skills blocked.

---

## Checklist

- [ ] `description` matches real user phrasing.  
- [ ] Procedure fits on one screen unless supporting files justify split.  
- [ ] Tested both **`/name`** and auto-invocation (if enabled).  
- [ ] No secrets in skill body — use env vars.  
