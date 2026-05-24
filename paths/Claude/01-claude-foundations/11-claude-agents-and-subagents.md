# Claude agents and subagents — delegation

**Goal:** define **subagents** in `.claude/agents/`, invoke them deliberately, and avoid losing ownership when work is delegated.

**Docs:** [Subagents](https://code.claude.com/docs/en/sub-agents) · **`/agents`** command

**Skills (procedures):** `10`. **Governance (tool limits):** `13`. **Multi-agent systems (architecture):** `18-multi-agent-systems/`.

Numerical prefixes = concept order only.

---

## What subagents are

Subagents are **specialized Claude configurations**:

- Custom system prompt / role  
- Tool allow and deny lists  
- Optional model override  
- Optional persistent memory (see subagent memory in docs)  
- May run in **foreground** or **background**

The **main thread** remains accountable for goal and acceptance — subagents are contractors, not owners.

---

## Where agent files live

| Scope | Path |
|-------|------|
| User | `~/.claude/agents/<name>.md` |
| Project | `.claude/agents/<name>.md` |

Format: **Markdown with YAML frontmatter** (same family as skills).

Manage in session: **`/agents`**.

---

## Example project subagent

`.claude/agents/code-reviewer.md`:

```markdown
---
name: code-reviewer
description: Read-only reviewer for diffs. Use before merge on risky changes.
tools: Read, Grep, Glob
model: inherit
---

You are a senior reviewer. Do not edit files.

For each finding provide:
- Severity (blocker / major / minor)
- File:line
- Falsifiable issue description
- Suggested fix direction (no full rewrites)

Refuse to approve if tests are missing for behavior change.
```

---

## Invocation patterns

| Pattern | How |
|---------|-----|
| Explicit | Settings key `"agent": "code-reviewer"` or `/agents` UI |
| Skill-driven | Skill with `context: fork` runs in subagent |
| Bundled | `/batch`, `/code-review` orchestrate subagents internally |
| Background | `/tasks`, `/background` — monitor with `claude agents` |

**Settings `agent` field:** run main thread **as** named subagent for a session slice — see [invoke subagents explicitly](https://code.claude.com/docs/en/sub-agents#invoke-subagents-explicitly).

---

## Foreground vs background

| Mode | Use |
|------|-----|
| **Foreground** | Short exploration; result merges back immediately |
| **Background** | Long research; parent continues; check `/tasks` |

**Lab discipline:** parent prompt must state **acceptance criteria** and **files in scope** before spawning.

---

## Worktrees and `/batch`

`/batch` decomposes large work into parallel units in **git worktrees** — each unit may run a subagent.

Requires git repo; review plan before approval — blast radius is multi-PR.

See [worktrees](https://code.claude.com/docs/en/worktrees) and [Run agents in parallel](https://code.claude.com/docs/en/agents).

---

## Agent design template

| Field | Content |
|-------|---------|
| **ROLE** | One sentence persona |
| **IN SCOPE** | Files, domains, tools |
| **OUT OF SCOPE** | Edits, prod access, secrets |
| **TOOLS** | Minimal allow list |
| **OUTPUT** | Structure of return packet |
| **HANDOFF** | What parent must verify |

---

## Multi-agent vs subagents (syllabus map)

| Foundations (`11`) | Later areas |
|--------------------|-------------|
| Single repo subagent files | `18-multi-agent-systems/` — Planner/Architect/QA roles |
| `/agents`, `/batch` | `19-agent-orchestration/` — routing |
| | `20-multi-agent-state-management/` — shared state |

Learn **file format and `/agents` here**; learn **system design there**.

---

## Lab

| Step | Action |
|------|--------|
| 1 | Add read-only `code-reviewer` agent |
| 2 | Make a small change; invoke reviewer on `/diff` scope |
| 3 | Compare review quality vs same ask in main thread without agent |
| 4 | Document one finding parent must **independently verify** |
| 5 | Optional: background task for “grep deprecated API usages” — list via `/tasks` |

---

## Anti-patterns

| Bad | Good |
|-----|------|
| Subagent implements without plan | Plan approved; subagent executes slice |
| Full tool access on reviewer | Read-only tools |
| Trust subagent summary blindly | Parent checks file:line |
| Many overlapping agents | Few roles with clear boundaries |

---

## Checklist

- [ ] Agent file committed or documented if user-scoped only.  
- [ ] Tools are **minimal** for role.  
- [ ] Parent acceptance criteria written before delegation.  
- [ ] I know **`/agents`** and **`/tasks`** for this install.  
