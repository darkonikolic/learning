# Sandbox thinking

Sandbox is not one thing. It is a spectrum of isolation choices made before anything runs.

The working definition: a sandbox is a controlled execution environment where Claude's actions have a bounded blast radius. Design the sandbox by answering one question first: "if this goes wrong, what breaks?" The answer tells you which isolation level to apply. If the answer is "everything on my machine," you have no sandbox.

---

## Why sandbox matters when working with Claude

Claude Code executes code, runs shell commands, writes and deletes files, makes git commits, and calls external services. Every one of those capabilities is useful. Every one of them can cause damage without isolation.

Without isolation:
- A bad agent action can corrupt your working tree mid-feature
- Claude reads `.env` and the actual values appear in a completion or log
- A misunderstood `rm` command deletes files with no recovery path
- A test that makes an external API call runs unreviewed against a production endpoint

With isolation:
- Failure is contained to the isolated unit
- Damage is reversible (git revert, worktree delete, container stop)
- The scope of what went wrong is visible and bounded

The point is not to prevent Claude from doing useful things. The point is to make sure "useful things going wrong" has a small, recoverable blast radius.

---

## Isolation levels — from light to heavy

| Level | Mechanism | What it isolates | Cost |
|-------|-----------|-----------------|------|
| 1 — Git worktree | `isolation: "worktree"` in Agent tool | Git history, file changes | Near zero |
| 2 — Permission allowlist | `settings.json` allow/deny | Which shell commands Claude can run | Near zero |
| 3 — Hooks | Pre/post tool hooks in `settings.json` | Validate intent before execution | Low |
| 4 — Docker container | `docker run` with mount and network policy | Filesystem, network, processes | Medium |
| 5 — Full sandbox | Docker + `--network none` + resource limits | Everything reachable from the process | High |

These levels compose. Level 1 + 2 is the baseline for normal development. Level 4 + 2 is appropriate when Claude is running code you haven't reviewed. Level 5 is appropriate for untrusted or generated scripts.

---

## When to use which level

| Task | Isolation level |
|------|----------------|
| Normal feature development | Level 1 + 2 |
| Risky refactor touching many files | Level 1 (worktree) + 2 |
| Running generated Go scripts | Level 4 |
| Agent executes arbitrary shell scripts | Level 4–5 |
| Integration tests that need external services | Level 4 (Docker Compose) |
| Production-adjacent work | Level 3–4 |
| Read-only exploration, no file writes | Level 2 only |

When in doubt, add the next level. The cost of over-isolation is a slightly slower workflow. The cost of under-isolation is a corrupted repo or an exposed secret.

---

## The three boundaries to name before execution

Every sandbox design has three boundaries. Name them explicitly before Claude runs anything non-trivial:

**Isolation boundary** — what the tool physically cannot reach. Example: a Docker container with `--network none` cannot reach the internet. A worktree cannot affect `main`.

**Permission boundary** — what the tool is authorized to do within reach. Example: Claude can read `.go` files but the deny list blocks `cat ~/.ssh/*`. Reaching a file and being allowed to read it are separate questions.

**Blast radius** — worst plausible outcome if the boundary fails. Example: "If Claude misunderstands the rm command, the worst case is deleting files inside the worktree only, which are recoverable via git." Write this sentence. If you cannot write it, the sandbox is not designed yet.

---

## The reversibility principle

Before any non-trivial action, ask: "can I undo this?"

Classify actions into two columns:

| Reversible | Irreversible |
|-----------|-------------|
| git commit (can revert) | git push to shared remote |
| file write (can git restore) | file write to path outside git |
| test run — no side effects | database DROP or TRUNCATE |
| container created | secret exposed in log or completion |
| worktree created | email sent, webhook triggered |

Irreversible actions require explicit human approval. This is not a preference — it is the rule. Automating irreversible actions without an approval gate is how production incidents happen in AI-assisted workflows.

For task-api (in-memory, no external systems): most actions are reversible. The exceptions are git push and any `rm` command outside the project root. Treat those as requiring confirmation.

---

## The sandbox design template

Use this template for any non-trivial project before running Claude in agent mode:

| Field | Fill in |
|-------|---------|
| WORKSPACE | Root path(s) where Claude may read/write; what is out of bounds |
| FILESYSTEM | Read-only vs read-write mounts; explicit ban list |
| NETWORK | Allow/deny posture; which hosts are reachable |
| SECRETS | Which credentials exist locally; which Claude must never see |
| TOOL ACCESS | Shell, git, database client — each with scope notes |
| PERMISSION MODEL | Actions mapped to allow/deny; default posture for unlisted |
| APPROVAL MODEL | Which actions require human confirmation before execution |
| ROLLBACK MODEL | How to revert: git, container restart, DB migration reversal |
| BLAST RADIUS | One sentence: worst case if this config is wrong |

For task-api, the template is short:

| Field | Value |
|-------|-------|
| WORKSPACE | `~/projects/task-api` only |
| FILESYSTEM | Read-write inside project root; deny traversal to `$HOME` |
| NETWORK | None for tests; localhost for manual API calls |
| SECRETS | No production secrets; `.env` in `.claudeignore` |
| TOOL ACCESS | `go`, `git`, `curl localhost` — no cloud CLIs |
| PERMISSION MODEL | Default allow inside project; deny `find /`, `cat ~/.ssh/*` |
| APPROVAL MODEL | Confirm before `git push`; confirm before any `rm` |
| ROLLBACK MODEL | `git revert` or worktree delete |
| BLAST RADIUS | Worst case: corrupted files inside task-api repo, recoverable via git |

---

## Weak vs strong execution patterns

| Weak | Strong |
|------|--------|
| Claude → shell → full host authority | Claude → declared workspace → scoped permissions → approved destructive steps |
| "Run whatever tests you need to" | "Run `go test ./...` inside the project root only" |
| No `.claudeignore` | `.claudeignore` excludes `.env`, keys, secrets |
| Auto-approve all confirmations | Read what Claude proposes before approving |
| Isolation added after something goes wrong | Isolation designed before the session opens |
| Blast radius never named | Blast radius written down in one sentence |

The weak pattern is faster in the short term and expensive when something goes wrong. The strong pattern adds five minutes of setup and removes the category of incident where you lose work or expose credentials.

---

## How isolation levels compose in practice

No project uses a single isolation level. They compose — each layer covers a different attack surface and each costs almost nothing when added deliberately at the start.

A realistic setup for a Go microservice under active development:

1. **Level 2 (permission allowlist)** — set once in `.claude/settings.json`. Denies `rm -rf`, `git push --force`, filesystem traversal outside project root. Cost: 15 minutes.

2. **Level 1 (worktree isolation)** — used for any agent that writes files. The default assumption when running an implementation agent. Cost: zero — Claude Code handles it automatically when `isolation: "worktree"` is set.

3. **Level 4 (Docker for test runs)** — tests run inside a container with `--network none` and read-only source mount. Docker image is built once and cached. Cost: the first build (a few minutes); subsequent runs add ~1 second overhead.

Together these three levels cover: accidental branch corruption, filesystem escape, external network calls from test code, and runaway shell commands. Level 3 (hooks) is added when the project involves external systems or production-adjacent work. Level 5 (full sandbox) is added when running untrusted or unreviewed scripts.

The composition approach means you apply only what the project actually needs, you understand why each layer is present, and you can explain the blast radius at every level.

---

## Checklist

- [ ] I can explain what "blast radius" means for the project I am working on right now.
- [ ] I have identified which isolation level is appropriate for the next Claude session.
- [ ] I know which actions in this project are irreversible and require explicit approval.
- [ ] I have named the three boundaries: isolation, permission, blast radius.
- [ ] I have completed the sandbox design template for at least one project.
- [ ] I understand the difference between "Claude cannot reach X" and "Claude is not allowed to access X."
- [ ] I know the difference between worktree isolation and Docker isolation and when each applies.
