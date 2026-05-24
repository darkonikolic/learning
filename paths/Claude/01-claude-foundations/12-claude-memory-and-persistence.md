# Claude memory and persistence — CLAUDE.md and auto memory

**Goal:** design **what persists across sessions** — your instructions, modular rules, and Claude’s **auto memory** — without confusing context with enforced config.

**Docs:** [How Claude remembers your project](https://code.claude.com/docs/en/memory) · **`/memory`**, **`/init`**

**Rules:** `09`. **Skills (procedures):** `10`. **Conceptual tiers:** `16-memory-systems/` (deeper).

Numerical prefixes = concept order only.

---

## Two memory systems

| System | Who writes | Content | Command |
|--------|------------|---------|---------|
| **CLAUDE.md + rules** | You | Instructions, standards, layout | `/memory`, `/init` |
| **Auto memory** | Claude | Learned preferences, build quirks | `/memory` to view/toggle |

Both load at session start. They are **context**, not hard enforcement — **specific, concise** instructions work best.

Auto memory loads **first ~200 lines or 25KB** — do not rely on it for critical safety policy (use **permissions** + **hooks** in `13`).

---

## CLAUDE.md locations (load order — broad → specific)

| Scope | Location |
|-------|----------|
| Managed (org) | OS-specific managed path — IT controlled |
| User | `~/.claude/CLAUDE.md` |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` |
| Local personal | `./CLAUDE.local.md` (gitignore) |

**Subdirectory CLAUDE.md** files load **lazily** when Claude accesses files there — good for monorepo packages.

**Imports:** `@path/to/file` in CLAUDE.md pulls content at launch (max depth 5).

---

## What belongs in CLAUDE.md

Add when:

- Claude repeats the same mistake  
- Review catches missing codebase knowledge  
- You re-type the same correction every session  

**Include:** build/test commands, architecture one-liner, naming conventions, “always X” facts.

**Exclude:** long procedures → **skill** (`10`); file-type policy → **`.claude/rules/`** (`09`).

**Size target:** under **~200 lines** per file — use path rules for bulk.

---

## `.claude/rules/` — modular memory

Path-scoped rules reduce always-on token cost. See `09-claude-rules-authoring.md`.

Use **`/memory`** or **`InstructionsLoaded` hook** to debug what loaded when.

---

## Auto memory

| Action | How |
|--------|-----|
| View entries | `/memory` |
| Disable | `/memory` or `autoMemoryEnabled: false` in settings |
| Custom directory | `autoMemoryDirectory` in user settings |

Subagents can maintain **separate auto memory** — see subagent docs.

**Hygiene:** periodically review auto memory for stale or wrong “facts”; delete bad entries.

---

## Bootstrap — `/init`

| Mode | Behavior |
|------|----------|
| Default `/init` | Analyze repo; suggest or extend CLAUDE.md |
| `CLAUDE_CODE_NEW_INIT=1` | Interactive: CLAUDE.md, skills, hooks proposal before write |

Run **`/init`** on new repo; **refine** with human knowledge Claude cannot infer (secrets handling, team quirks).

---

## Memory vs compaction

| Event | CLAUDE.md / rules | Chat scrollback |
|-------|-------------------|-----------------|
| `/compact` | Survive per [compaction docs](https://code.claude.com/docs/en/context-window#what-survives-compaction) — verify | Summarized |
| `/clear` | Reload on new session | Gone (recover via `/resume`) |

**Critical decisions** belong in **files** (`docs/plans/`, CLAUDE.md, STATE.md), not only chat.

---

## Conceptual tiers (bridge to `16-memory-systems/`)

| Tier | Claude Code artefact |
|------|----------------------|
| Working | Current prompt + attachments |
| Episodic | Chat history, `/resume`, export |
| Semantic | CLAUDE.md, rules, PROJECT.md |
| Persistent policy | settings permissions, hooks |

Use this vocabulary when designing larger systems — not as duplicate storage everywhere.

---

## Lab

| Step | Action |
|------|--------|
| 1 | Run `/init` on sample repo; trim generated CLAUDE.md to essentials |
| 2 | Add 5 bullets Claude could not infer |
| 3 | Move one long procedure from CLAUDE.md to new skill |
| 4 | Add path rule for one module — remove duplicate from CLAUDE.md |
| 5 | `/context` — compare memory footprint before/after |
| 6 | Review auto memory; delete one stale entry |

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Ignores instruction | Too vague? Contradicts another rule? |
| Never sees instruction | Wrong path scope? File not in lazy-loaded tree? |
| Context bloat | CLAUDE.md too long — split to rules |
| Wrong “facts” | Stale auto memory |

---

## Checklist

- [ ] CLAUDE.md has **build/test** commands verified working.  
- [ ] Procedures live in **skills**, not CLAUDE.md walls.  
- [ ] Path rules cover module-specific policy.  
- [ ] I reviewed **auto memory** this month.  
- [ ] `/context` used once to validate memory cost.  
