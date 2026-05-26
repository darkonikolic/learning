# Large-repo navigation and archaeology

`01-session-ownership.md` and `03-context-ownership.md` apply to any repo. **Large monoliths** need explicit **archaeology**: finding owners, call paths, and blast radius before Claude touches code.

Claude Code tools: **Grep**, **Glob**, **Read**, optional **MCP** (code search, CI, tickets). You steer the search; Claude does not “feel” the whole tree.

---

## Ownership discovery

**Goal:** know which package or module owns the behavior you will change.

| Technique | When |
|-----------|------|
| **Route → handler** | HTTP: find route registration, follow to controller/handler |
| **Error message** | Stack trace points to file:line — start there |
| **Grep symbol** | `grep -r "CompleteTask" --include='*.go'` |
| **Glob by convention** | `**/tasks/**`, `internal/**`, `src/Module/**` |
| **SPEC boundary** | `06-specification-first/02-boundaries-nfr-and-constraints.md` names owner package |

**Prompt pattern:**

```
Do not edit yet. Map ownership for PATCH /tasks/:id/complete:
- route registration file
- handler file
- store/domain file
- existing tests
Return paths only; no code.
```

You verify paths with Read before execute.

---

## Dependency archaeology

**Goal:** what breaks if this type or function changes?

| Step | Action |
|------|--------|
| 1 | Grep interface and struct name across repo |
| 2 | Grep constructor / `New*` / DI wiring (framework service config or Go wire) |
| 3 | List **callers** — not only definitions |
| 4 | Note generated code (`vendor/`, `*/mocks/`) — exclude from edit scope |

**Typical layouts:** framework service YAML or attributes; domain vs infrastructure packages; Go `internal/` import boundaries.

Record findings in frame brief or plan task: “callers: X, Y.”

---

## Call path tracing

Trace **one request** end-to-end before multi-file edits:

```
HTTP entry → middleware → handler → service → repository → DB
```

For task-api scale, trace is short. For large services, trace may cross many layers.

**Claude prompt:**

```
Trace call path for [feature] from route to persistence.
List each function/method with file:line.
Stop at store/repository boundary.
```

You spot-check two hops yourself — Claude can miss dynamic dispatch and event subscribers.

---

## Cross-module navigation

| Pattern | Risk |
|---------|------|
| Shared DTO in `common/` | Wide blast radius |
| Event / message bus | Hidden consumers |
| Interface in domain, impl in infra | Edit wrong package |
| Feature flags | Dead branch looks live |

**Rule:** name **allowed packages** in the execute prompt. “Only `tasks/` and `main.go`.”

---

## Boundary discovery

Boundaries are where **invariants change** — HTTP vs domain vs persistence.

Ask before coding:

- Who parses JSON — handler only?
- Who assigns IDs — store only?
- Who maps errors to status codes — handler only?

Align with SPEC **Boundary** section. If missing, write it before execute (`06-specification-first/02-boundaries-nfr-and-constraints.md`).

---

## Change impact estimation

Before approve on plan:

| Question | Evidence |
|----------|----------|
| How many files will change? | Plan task list |
| How many callers of changed API? | Grep count |
| Tests that must move? | Grep `_test.go` import paths |
| Config / migration? | Schema, env, DI |

**Regression surface map** (minimal):

```markdown
## Regression surface — [feature]
- Direct: tasks/handler.go, tasks/store.go
- Callers: main.go route table
- Tests: tasks/store_test.go, handler tests if any
- Out of scope: other packages (list explicitly)
```

Attach to `docs/plans/<phase>-context.md` or plan task 1.

---

## Claude session tactics for large repos

| Tactic | Why |
|--------|-----|
| **Scope by directory** | Prevents drive-by refactors |
| **Read slices** | One handler + one store file, not whole module tree |
| **Map-then-edit** | Two messages: archaeology, then execute |
| **Worktree** | Long branch experiments (`09-sandbox-safe-execution/02-worktree-isolation.md`) |
| **`.claudeignore`** | Exclude `vendor/`, `node_modules/`, generated |

---

## Checklist

- [ ] I map ownership before asking for implementation.
- [ ] I grep callers before changing exported symbols.
- [ ] I trace one call path for non-trivial features.
- [ ] I document regression surface in plan or frame brief.
- [ ] I scope execute prompts to named packages.
