# Worktree isolation

Git worktree is the cheapest, highest-leverage isolation mechanism available in Claude Code. Cost: near zero. Effect: Claude's file changes never touch your working branch until you explicitly merge them.

---

## What a git worktree is

A linked working tree: the same git repository, checked out into a different directory, on a different branch.

Normal state: one repository, one working directory, one branch.
Worktree state: one repository, two working directories, two branches. Both see the full git history. Changes in one do not appear in the other until merged.

```
.git/                        ← shared repository
task-api/                    ← your main working tree (branch: main)
/tmp/task-api-agent-abc123/  ← worktree (branch: agent/refactor-handlers)
```

If the agent makes a mess in the worktree, you delete the worktree. Your `main` branch is untouched. The worktree branch is deleted. Nothing persists.

If the agent succeeds, you review the diff between `main` and the agent's branch, then merge when satisfied.

---

## How Claude Code uses worktrees

When you pass `isolation: "worktree"` to an Agent tool call, Claude Code:

1. Creates a new git branch from the current HEAD
2. Checks that branch out into a new temporary worktree directory
3. Runs the agent in that directory — all file reads, writes, and git commits land in the worktree
4. Returns the worktree path and branch name when the agent completes
5. If the agent makes no changes: automatically removes the worktree and deletes the branch

Your main working directory is untouched throughout.

Example Agent invocation with isolation:

```
Agent({
  description: "Refactor task handlers to use repository pattern",
  isolation: "worktree",
  prompt: "Refactor internal/handler/task.go to use the repository pattern defined in internal/store/store.go. Extract handler logic into handler methods. Keep all existing tests passing."
})
```

What you receive back: the worktree path and branch name. From there, review and decide.

---

## When to always use worktree isolation

Use worktree isolation when:
- The agent is implementing a feature that touches more than three files
- The agent is performing a refactor (file moves, interface changes, method renames)
- You want to review changes before they land on your current branch
- You are running two agents in parallel on the same repository
- You are not sure what files the agent will touch

When worktree isolation is NOT needed:
- Read-only agents (exploration, planning, code review without `--fix`)
- Single-file changes you will review inline before accepting
- Agents that only run tests and produce no file writes
- `/plan` or `/spec` runs that output only to chat

Rule of thumb: if the agent writes files, use worktree isolation.

---

## Reviewing worktree output

After an agent with worktree isolation completes:

```bash
# See all worktrees and their branches
git worktree list

# Review what changed
git diff main...agent/refactor-handlers

# Review commit-by-commit
git log main..agent/refactor-handlers --oneline

# Run tests on the worktree branch without merging
cd /tmp/task-api-agent-abc123
go test ./...
```

Three outcomes:

**Changes look good:** merge or create a PR.
```bash
git checkout main
git merge agent/refactor-handlers
# or: gh pr create --head agent/refactor-handlers
```

**Changes need minor adjustment:** edit in the worktree, commit, then merge.
```bash
cd /tmp/task-api-agent-abc123
# make edits
git add -p
git commit -m "fix: adjust handler signature per review"
cd ~/projects/task-api
git merge agent/refactor-handlers
```

**Changes are wrong or unwanted:** delete the worktree and branch.
```bash
git worktree remove /tmp/task-api-agent-abc123
git branch -d agent/refactor-handlers
```

---

## Parallel agents with worktrees

Each agent in its own worktree means no write conflicts. Two agents can work on the same repository simultaneously without corrupting each other's changes.

```
main branch
├── worktree-A (branch: agent/add-get-endpoint)   ← Agent 1: GET /tasks
└── worktree-B (branch: agent/add-patch-endpoint) ← Agent 2: PATCH /tasks/:id/complete
```

Merge order matters if the agents touch overlapping files. Merge whichever is simpler first, then rebase the second onto the updated main before merging. Overlapping file conflicts are resolved at merge time, not during execution — the agents ran cleanly in isolation.

For task-api parallel work:
- Agent 1 adding `GET /tasks` touches `internal/handlers/tasks.go` and `main.go`
- Agent 2 adding `PATCH /tasks/:id/complete` touches the same files
- Both agents run in their own worktrees without conflict
- At merge time: resolve the handler file conflict (typically additive, low risk)

---

## Manual worktree workflow (without Claude Code automation)

Useful to understand what Claude Code does under the hood, and for cases where you want to set up a worktree manually before handing it to an agent:

```bash
# Create a branch and worktree in one command
git worktree add /tmp/task-api-sandbox -b sandbox/manual-test

# Work in the worktree
cd /tmp/task-api-sandbox
echo "// sandbox test" >> main.go
git add main.go && git commit -m "test: sandbox change"

# Verify main working tree is untouched
cat ~/projects/task-api/main.go | grep "sandbox" # returns nothing

# Review the diff
git diff main...sandbox/manual-test

# Clean up without merging
git worktree remove /tmp/task-api-sandbox
git branch -d sandbox/manual-test
```

---

## Worktree state and cleanup

Worktrees that are not cleaned up accumulate. Check and manage them:

```bash
# List all worktrees with their paths and branches
git worktree list

# Remove a specific worktree (also works if the directory was manually deleted)
git worktree remove /tmp/task-api-agent-abc123

# Prune worktrees whose directories no longer exist
git worktree prune

# Remove the leftover branch after worktree removal
git branch -d agent/refactor-handlers
```

Claude Code automatically removes worktrees when the agent makes no changes. Worktrees from successful or failed agents are left for you to review and clean up. Pruning occasionally is good hygiene — orphaned worktree entries consume no disk but clutter `git worktree list`.

---

## Worktree isolation vs other mechanisms

| Mechanism | Protects | Doesn't protect |
|-----------|----------|----------------|
| Worktree isolation | Your working branch from agent file changes | Secrets the agent can read, shell commands outside git |
| Permission allowlist | Shell commands Claude can run | File-level git changes |
| `.claudeignore` | Which files Claude reads | What Claude does with files it can read |
| Docker | Filesystem and network | Git history (unless repo is outside container) |

Worktree + permission allowlist covers the common cases. Docker adds protection when the risk is in what the code *does* at runtime, not just what files it touches.

---

## Checklist

- [ ] I understand what a linked working tree is and how it differs from a branch.
- [ ] I know what Claude Code does automatically when `isolation: "worktree"` is set.
- [ ] I can list worktrees, review the diff, merge, and delete a worktree manually.
- [ ] I know which agent tasks require worktree isolation and which do not.
- [ ] I understand how to run two agents in parallel on the same repo using separate worktrees.
- [ ] I have created a worktree manually, made a change, verified the main tree is unaffected, and cleaned it up.
- [ ] I know how to prune stale worktree entries with `git worktree prune`.
