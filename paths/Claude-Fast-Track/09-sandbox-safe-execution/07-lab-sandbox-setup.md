# Lab: sandbox setup for task-api

This lab configures and tests every isolation layer covered in this module. Each part has a concrete deliverable. Do not proceed to the next part until the current deliverable is verified.

All steps assume you are working in the `task-api` directory from earlier labs. If it does not exist, create the skeleton first:

```bash
mkdir -p ~/projects/task-api
cd ~/projects/task-api
git init
go mod init task-api
mkdir -p internal/store internal/handlers .claude/hooks
```

---

## Part 1: Git worktree isolation

**Goal:** create a worktree manually, make a change, verify isolation, review the diff, clean up.

**Step 1.** Confirm you are on `main` (or your default branch):

```bash
git -C ~/projects/task-api branch
```

**Step 2.** Create a worktree on a new branch:

```bash
git -C ~/projects/task-api worktree add /tmp/task-api-sandbox -b sandbox/worktree-lab
```

**Step 3.** Add a file inside the worktree — not from the project directory:

```bash
echo "// worktree isolation test" > /tmp/task-api-sandbox/sandbox_test_file.go
cd /tmp/task-api-sandbox && git add sandbox_test_file.go && git commit -m "test: worktree isolation file"
```

**Step 4.** Verify the file does NOT exist in your main working tree:

```bash
ls ~/projects/task-api/sandbox_test_file.go
# Expected: No such file or directory
```

**Step 5.** Review the diff between `main` and the worktree branch:

```bash
git -C ~/projects/task-api diff main...sandbox/worktree-lab
```

Verify only the test file appears in the diff.

**Step 6.** Clean up the worktree and branch:

```bash
git -C ~/projects/task-api worktree remove /tmp/task-api-sandbox
git -C ~/projects/task-api branch -d sandbox/worktree-lab
```

**Step 7.** Verify cleanup:

```bash
git -C ~/projects/task-api worktree list
# Expected: only the main worktree listed
```

Deliverable: worktree created, isolated change confirmed, worktree removed cleanly.

---

## Part 2: Secret isolation

**Goal:** confirm Claude cannot read `.env` after `.claudeignore` is in place.

**Step 8.** Create a test `.env` file in task-api:

```bash
cat > ~/projects/task-api/.env << 'EOF'
PORT=8080
DEBUG_SECRET=this-value-should-never-reach-claude-xk9z2m
DATABASE_URL=postgres://admin:hunter2@localhost/tasks
EOF
```

**Step 9.** Create `.claudeignore`:

```bash
cat > ~/projects/task-api/.claudeignore << 'EOF'
.env
.env.*
*.pem
*.key
*credentials*
*secrets*
EOF
```

**Step 10.** Create `.env.example` (the template that IS committed):

```bash
cat > ~/projects/task-api/.env.example << 'EOF'
PORT=8080
DEBUG_SECRET=your-debug-secret-here
DATABASE_URL=postgres://user:password@localhost/tasks
EOF
```

**Step 11.** Update `.gitignore` to exclude `.env`:

```bash
cat >> ~/projects/task-api/.gitignore << 'EOF'
.env
.env.*
EOF
```

**Step 12.** Open Claude Code in the task-api directory and ask:

```
What is the value of DEBUG_SECRET in this project?
```

Expected behavior: Claude reports it cannot read `.env` and can only see `.env.example`. The value `this-value-should-never-reach-claude-xk9z2m` must not appear in the response.

If the value appears: your `.claudeignore` is not being applied. Verify the file is named exactly `.claudeignore` (not `claudeignore` or `.claudeignore.txt`) and is in the project root.

Deliverable: `.env` exists with a test secret. `.claudeignore` and `.env.example` created. Claude cannot read the actual secret value.

---

## Part 3: Permission restrictions

**Goal:** verify the deny list blocks filesystem escape attempts.

**Step 13.** Create or update `.claude/settings.json` in the task-api directory:

```bash
mkdir -p ~/projects/task-api/.claude
cat > ~/projects/task-api/.claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(go test ./...:*)",
      "Bash(go build ./...:*)",
      "Bash(go vet ./...:*)",
      "Bash(ls:*)",
      "Bash(find . -name '*.go':*)",
      "Bash(cat:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)"
    ],
    "deny": [
      "Bash(find / :*)",
      "Bash(find /etc:*)",
      "Bash(find ~ :*)",
      "Bash(cat ~/.ssh/*:*)",
      "Bash(cat /etc/*:*)",
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)"
    ]
  }
}
EOF
```

**Step 14.** Open Claude Code in task-api and ask:

```
Show me what's in ~/.ssh/
```

Expected behavior: Claude refuses the operation, citing the deny list or a permission error. If Claude returns the contents of `~/.ssh/`, the deny list is not applied — verify `settings.json` is valid JSON and in the correct location (`.claude/settings.json` inside the project root).

**Step 15.** Verify a safe operation still works:

```
Run: ls internal/
```

Expected behavior: Claude runs `ls internal/` and returns the directory listing.

Deliverable: deny list blocks `~/.ssh/` access. Safe operations (ls, go test) are not blocked.

---

## Part 4: Docker sandbox for tests

**Goal:** run `go test ./...` inside Docker with network isolation and read-only source mount.

**Step 16.** Create `Dockerfile.sandbox` in task-api:

```bash
cat > ~/projects/task-api/Dockerfile.sandbox << 'EOF'
FROM golang:1.22-alpine

WORKDIR /app

# Copy only dependency files — source is mounted at runtime
COPY go.mod go.sum* ./
RUN go mod download 2>/dev/null || true

EOF
```

Note: `go.sum` may not exist yet if no tests have been written. The `|| true` handles the empty module case.

**Step 17.** Build the sandbox image:

```bash
docker build -f ~/projects/task-api/Dockerfile.sandbox -t task-api-sandbox ~/projects/task-api
```

**Step 18.** Create a minimal test file so `go test ./...` has something to run:

```bash
cat > ~/projects/task-api/main_test.go << 'EOF'
package main

import "testing"

func TestSanity(t *testing.T) {
    if 1+1 != 2 {
        t.Fatal("arithmetic broken")
    }
}
EOF
```

Also create a `main.go` if it does not exist:

```bash
cat > ~/projects/task-api/main.go << 'EOF'
package main

func main() {}
EOF
```

**Step 19.** Run tests inside the Docker sandbox:

```bash
docker run --rm \
  --network none \
  --read-only \
  --mount type=bind,source=$(cd ~/projects/task-api && pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  --mount type=tmpfs,target=/root/.cache \
  task-api-sandbox \
  sh -c "cd /app && go test ./..."
```

Expected output: `ok      task-api    0.001s` (or similar passing output).

**Step 20.** Verify that the network restriction actually blocks outbound connections:

```bash
docker run --rm \
  --network none \
  golang:1.22-alpine \
  sh -c "wget -T 2 -q https://google.com && echo 'FAIL: network accessible' || echo 'PASS: network blocked'"
```

Expected output: `PASS: network blocked`

**Step 21.** Verify that the read-only mount prevents writes to source:

```bash
docker run --rm \
  --read-only \
  --mount type=bind,source=$(cd ~/projects/task-api && pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  golang:1.22-alpine \
  sh -c "echo 'test' > /app/unauthorized-write.txt && echo 'FAIL: wrote to source' || echo 'PASS: write blocked'"
```

Expected output: `PASS: write blocked`

Deliverable: `go test ./...` passes in the Docker sandbox. Network restriction verified. Read-only mount verified. No file `unauthorized-write.txt` exists in `~/projects/task-api/`.

---

## Part 5: Dangerous action policy test

**Goal:** trigger a blocked action and observe the policy enforcing.

**Step 22.** Open Claude Code in task-api and ask:

```
Run git push --force origin main
```

Expected behavior: Claude refuses with a message indicating the command is blocked or dangerous. The push does not execute.

If the push executes (or Claude asks for your remote credentials and pushes): the deny list is not applied. Verify `settings.json` syntax and location.

**Step 23.** Ask Claude:

```
I want to delete the entire vendor directory with rm -rf. Can you do that?
```

Expected behavior: Claude refuses the `rm -rf` operation based on the deny list. Claude may suggest `go mod vendor` cleanup as an alternative.

**Step 24.** Practice the propose-then-execute pattern. Ask Claude:

```
I need to add a GET /tasks handler. Before writing any code, propose the complete list
of files you will touch and the changes you will make. Do not write any code yet.
```

Review Claude's proposal. Identify at least one thing you would change or clarify. Send the clarification. Only then say "approved, proceed."

Deliverable: blocked operations (force push, rm -rf) refused by Claude. Propose-then-execute pattern practiced once.

---

## Part 6: Full sandbox review

**Goal:** verify the complete sandbox template for task-api is filled in.

**Step 25.** Write the sandbox template for task-api. Create `docs/sandbox-template.md`:

```bash
mkdir -p ~/projects/task-api/docs
```

Fill in the template from module 01:

```markdown
# Sandbox template: task-api

| Field | Value |
|-------|-------|
| WORKSPACE | ~/projects/task-api only |
| FILESYSTEM | Read-write inside project root; .claudeignore blocks .env, *.key; deny list blocks ~/ and /etc traversal |
| NETWORK | --network none for Docker tests; localhost only for manual runs |
| SECRETS | No production secrets; .env in .claudeignore; .env.example committed with placeholders |
| TOOL ACCESS | go, git, ls, find (in project), cat (non-secret files) |
| PERMISSION MODEL | Allow list for safe ops; deny list for rm -rf, force push, filesystem escape |
| APPROVAL MODEL | Confirm before git push; forbidden class requires manual execution |
| ROLLBACK MODEL | git revert for any committed change; worktree delete for agent changes |
| BLAST RADIUS | Worst case: corrupted files inside task-api repo, recoverable via git |
```

**Step 26.** Verify the file exists and is complete:

```bash
cat ~/projects/task-api/docs/sandbox-template.md
```

All nine fields must be filled in with task-api-specific values, not placeholders.

Deliverable: `docs/sandbox-template.md` exists with all fields filled in.

---

## Validation: can you answer these questions without looking?

After completing all six parts, answer these without checking:

1. What happens to an agent's file changes when `isolation: "worktree"` is set and the agent makes no changes?
2. What does `--network none` restrict that Claude's permission deny list does not?
3. Which file prevents Claude from reading `.env`, and which file prevents `.env` from being committed?
4. What is the difference between a NEEDS_APPROVAL action and a DANGEROUS — HUMAN MUST EXECUTE action?
5. What does `git worktree prune` do and when should you run it?

If you cannot answer any of these: re-read the corresponding module file, then come back.

---

## Checklist

- [ ] Git worktree created, isolated change confirmed, worktree and branch cleaned up.
- [ ] `.env` file created with test secret value that is not a real credential.
- [ ] `.claudeignore` created and verified — Claude cannot read the `.env` contents.
- [ ] `.env.example` created with placeholder values and committed.
- [ ] `settings.json` deny list blocks `~/.ssh/`, `rm -rf`, `git push --force`.
- [ ] Safe operations (ls, go test) confirmed to still work after deny list applied.
- [ ] `Dockerfile.sandbox` built successfully.
- [ ] `go test ./...` passes inside Docker with `--network none` and read-only source mount.
- [ ] `--network none` restriction verified: outbound connections blocked.
- [ ] Read-only mount verified: writes to source directory blocked.
- [ ] `git push --force` blocked by Claude when requested.
- [ ] `rm -rf` blocked by Claude when requested.
- [ ] Propose-then-execute pattern practiced: full proposal reviewed before approving.
- [ ] `docs/sandbox-template.md` filled in with all nine fields.
- [ ] I can explain the difference between worktree and Docker isolation without looking at notes.
