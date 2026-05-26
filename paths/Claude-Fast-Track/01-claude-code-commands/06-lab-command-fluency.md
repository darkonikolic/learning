# Lab — command fluency

## Objective

At the end of this lab you have:
- A working `task-api` git repo with a minimal project structure
- A CLAUDE.md file Claude can use from the first session
- Hands-on experience with the core slash commands
- A settings.json with at least one permission rule

This lab builds the foundation the remaining modules depend on. Do not skip it.

---

## Prerequisites

- Claude Code installed: `claude --version` returns a version string
- Go 1.21+ installed: `go version` returns a version string
- Git available: `git --version` returns a version string

---

## Step 1 — Create the toy project

Open a terminal. Run:

```bash
mkdir task-api
cd task-api
git init
go mod init github.com/yourname/task-api
```

Create a minimal main.go so the project has real content:

```go
package main

import (
    "log"
    "net/http"
)

func main() {
    mux := http.NewServeMux()
    // Handlers will be added in later modules
    log.Println("starting task-api on :8080")
    log.Fatal(http.ListenAndServe(":8080", mux))
}
```

Verify it compiles:

```bash
go build ./...
```

If it builds, continue. If it does not, fix the error before proceeding.

---

## Step 2 — Open Claude Code and run /help

Navigate to the task-api directory in your terminal. Open Claude Code:

```bash
claude
```

Type `/help` and read the full output. Note three commands you did not know existed before this module. Write them here (in your own notes — this lab does not generate files for you):

- Command 1: _______________
- Command 2: _______________
- Command 3: _______________

This is not busywork. `/help` output varies by Claude Code version and installed skills. What you see is authoritative for your install.

---

## Step 3 — Use /plan for project structure design

In your Claude Code session, run:

```
/plan Draft a file structure for a Go HTTP API with 3 endpoints: POST /tasks, GET /tasks, PATCH /tasks/:id/complete. No code yet — just the directory layout and what goes in each file.
```

Read Claude's proposed structure. It should propose something like:

```
task-api/
  main.go         — server setup and routing
  tasks/
    handler.go    — HTTP handlers for /tasks endpoints
    store.go      — database operations
    store_test.go — tests
  schema.sql      — database schema
  go.mod
```

**Edit one thing.** Pick one part of the proposed structure you would change — maybe the test file location, maybe you want a separate models.go, maybe you want an internal/ package structure. State your change:

```
I want to put the task model in tasks/model.go separately from the store.
```

Note how Claude responds to the edit in plan mode. It should adjust without executing anything.

You are practicing the plan-then-approve workflow. The plan lives in the chat for now. In module 02, you will write plans to `docs/plans/<phase>-plan.md` before executing.

---

## Step 4 — Check context with /context

Type `/context` in your session. Observe:

- How much of the context window is occupied
- What sources are consuming the most space (CLAUDE.md, rules, chat history, etc.)
- Whether the context feels proportionate to what you have done so far

In a fresh session with only a few messages, context should be low. Note the number. You will use this as a baseline.

---

## Step 5 — Run /compact and observe

Type `/compact` in your session.

After compaction, type `/context` again. Compare:

- How much context was freed
- Whether Claude still knows the project structure you discussed in step 3

Test by asking: "What file structure did we discuss for the task-api?" If Claude can still answer accurately, the important context survived compaction. If it cannot, note what was lost — this is a real lesson about when to write plans to disk.

---

## Step 6 — Create CLAUDE.md for the project

In your `task-api` directory (outside of Claude Code — in a regular text editor or a new terminal), create `CLAUDE.md`:

```markdown
# task-api

Go HTTP API for task management. stdlib net/http only. In-memory store for the whole track — no database.

## Build and test

go build ./...
go test ./...
go vet ./...

## Structure

main.go           — server setup, route registration
tasks/
  handler.go      — HTTP handlers (POST /tasks, GET /tasks, PATCH /tasks/:id/complete)
  store.go        — in-memory store
  store_test.go   — handler and store tests

## Conventions

- Handlers: func(w http.ResponseWriter, r *http.Request) only
- Store methods: return (T, error); never panic
- JSON errors: {"error": "message"}
- Verifiable contracts live in docs/specs/ — not only in chat

## Constraints

- No external packages beyond stdlib
- All tests pass before commit
- Never commit .env files
```

Save the file. Back in Claude Code, run:

```
/clear
```

Start a new session and ask: "What are the constraints for this project?" Claude should read CLAUDE.md and give you the correct constraints without re-prompting. If it does not, check the file is saved in the right directory.

---

## Step 7 — Find settings.json with /config

In Claude Code, type `/config` (or `/settings`). The settings UI opens.

Find where `settings.json` lives for this project. It should be at `.claude/settings.json` in your project directory (Claude Code creates the `.claude/` directory if it does not exist).

Create `.claude/settings.json` with a minimal permission configuration:

```json
{
  "permissions": {
    "allow": [
      "Bash(go build ./...)",
      "Bash(go test ./...)",
      "Bash(go vet ./...)",
      "Bash(git diff *)",
      "Bash(git status)",
      "Bash(git log *)"
    ],
    "ask": [
      "Bash(git commit *)",
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(**/.env.*)"
    ]
  }
}
```

Verify: ask Claude to run `go build ./...`. It should run without prompting (allowed). Ask Claude to check `git status`. Also allowed. Ask Claude "can you read the .env file?". It should report the action is denied.

---

## Step 8 — Commit what you have

In your terminal (outside Claude Code), run:

```bash
git add CLAUDE.md .claude/settings.json main.go go.mod
git commit -m "bootstrap task-api with CLAUDE.md and settings"
```

You now have a real project foundation. Every module from here builds on this.

---

## Verification questions

Before moving to module 02, confirm you can answer these without looking at notes:

1. What command shows you how much context window is in use?
2. What survives `/compact` that would not survive `/clear`?
3. Where does Claude read project instructions from at session start?
4. What does adding a path to `deny` in settings.json do that adding it to CLAUDE.md does not?
5. What does `/plan` mode prevent Claude from doing?

If you cannot answer any of these, re-read the relevant file from module 01 before continuing.

---

## Checklist

- [ ] `task-api/` directory exists with `go.mod` and `main.go` that compiles.
- [ ] `git init` ran and there is at least one commit.
- [ ] `CLAUDE.md` exists with build commands, structure, conventions, and constraints.
- [ ] `.claude/settings.json` exists with allow, ask, and deny rules.
- [ ] I ran `/help` and noted three commands I did not know.
- [ ] I used `/plan` mode and edited the proposed structure.
- [ ] I ran `/compact` and observed what survived.
- [ ] I can answer all five verification questions above.
