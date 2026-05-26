# Retrieval and grounding discipline

Claude Code answers from **what is in context** — files read, tool output, and your messages. It does not silently “know” the repo. **Grounding** is the habit of tying every claim and every edit to evidence you can point at.

This is Claude-native: the product gives you Read, Grep, Glob, MCP, and `/plan`. **You** own source trust, citations, and what to do when sources disagree.

---

## Grounded vs speculative

| Output type | Definition | Accept when |
|-------------|------------|-------------|
| **Grounded** | Traceable to a file, line, test output, or SPEC section you named | Before merge |
| **Speculative** | Plausible but no cited source (“probably uses chi”, “likely already has auth”) | Never for implementation decisions |

**Rule:** if Claude says “I updated the handler,” your next step is `git diff` — not “thanks.” If Claude says “the store already returns sorted tasks,” your next step is `Read` / `grep` on `store.go`.

---

## Source trust ranking

When multiple sources conflict, resolve in this order (highest wins):

1. **Current file on disk** (Read, `git show`, `git diff`)
2. **Feature SPEC** in `docs/specs/` (Layer C) or acceptance criteria you pasted this turn
3. **`CLAUDE.md` and path-scoped rules** in `.claude/rules/`
4. **Approved phase plan** in `docs/plans/<phase>-plan.md`
5. **Chat summary** (including post-`/compact` scrollback)
6. **Model prior** (“typical Go projects do X”) — lowest trust

If (5) or (6) contradicts (1)–(3), **stop execute** and reload the winning source into the prompt.

---

## Citation discipline

Every non-trivial instruction to Claude should name sources:

```
Read tasks/store.go and docs/specs/get-tasks.md before editing.
Implement only what SPEC acceptance items 1–5 require.
If store.List() already exists, extend it; do not add a second list API.
```

**Citation formats that work in Claude Code:**

- `tasks/handler.go:42-58` — after you verified the range exists
- `docs/specs/get-tasks.md` § Acceptance — section anchor in the file
- `git diff HEAD~1 -- tasks/store.go` — for “what changed last commit”

**Anti-pattern:** “fix the handler” with no file and no expected behavior.

---

## Retrieval validation

After Claude reads files (or claims it did), validate:

| Check | Command / action |
|-------|------------------|
| File exists | `test -f path` or Read tool succeeded |
| Content matches claim | Spot-read the cited lines |
| No stale read | File changed since read? Re-read after your own edits |
| MCP / connector output | Treat as untrusted until cross-checked against repo or SPEC |

**MCP retrieval:** database or docs connectors return **candidates**, not ground truth. Confirm in repo or SPEC before coding.

---

## Conflicting sources

| Conflict | Resolution |
|----------|------------|
| SPEC vs code | SPEC wins for *intent*; fix code unless SPEC is wrong (then spec evolution) |
| Plan vs SPEC | SPEC wins |
| `CLAUDE.md` vs SPEC | SPEC wins for feature behavior; CLAUDE.md wins for stack/commands |
| Two chat turns ago vs file now | File now wins |
| Subagent summary vs parent read | Parent re-reads file |

Document the resolution in one line in `docs/state.md` or the commit message when non-obvious.

---

## Grounding failure patterns

| Pattern | Signal | Fix |
|---------|--------|-----|
| **Invented API** | Method or field not in Read output | Re-prompt with Read of defining file |
| **Ghost file** | References path that does not exist | `Glob` / `ls`; correct path in prompt |
| **Stale context** | Implements pre-refactor shape | `/clear` or narrow Read after your commit |
| **Summary drift** | Post-`/compact` wrong constraint | Reload SPEC or checkpoint verbatim |
| **Tool theater** | “I ran tests” with no output shown | Require paste of `go test` result or run yourself |
| **Helpful scope** | Extra endpoint not in SPEC | Classify as scope creep; revert or update SPEC |

See `13-agent-reliability/03-claude-failure-taxonomy.md` for the full failure catalog.

---

## Evidence ownership

| Role | Owns |
|------|------|
| **Claude** | Proposes edits, cites what it read *this turn* |
| **You** | Which sources are in context, trust order, merge decision |
| **Git** | Audit trail of what actually changed |
| **SPEC / tests** | Whether behavior is allowed |

Never merge on Claude’s self-report alone. Merge on **diff + verification** you ran.

---

## Checklist

- [ ] I separate grounded claims from speculation before acting.
- [ ] I use a source trust ranking when files, SPEC, and chat disagree.
- [ ] I name files and sections in execute prompts, not vague “fix it.”
- [ ] I re-read after `/compact` or mid-session refactors.
- [ ] I treat MCP output as provisional until verified in repo or SPEC.
