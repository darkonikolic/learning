# Trust but verify

"An agent's summary of what it did is not proof that it did it."

This is the central principle of working effectively with AI agents. Violating it is the single most common mistake developers make when first using Claude Code for autonomous tasks.

---

## Why verification is non-optional

**Agents can hallucinate.** Hallucination is when a model generates confident output that is factually wrong. An agent can say "I created internal/handler/task.go with the GetAll handler" when the file doesn't exist. It is not lying — the model generated that summary because it matched its training patterns. The file does not exist.

**Agents can be partially wrong.** The file exists but the function signature is wrong. The tests pass but they test the wrong behavior. The handler is written but the status code is 200 instead of 201.

**Agents can misunderstand scope.** You said "implement GetAll." The agent implemented GetAll, added a second method you didn't ask for, changed a struct field name because it "looked inconsistent," and helpfully added imports you don't want. All of this while accurately reporting "I implemented GetAll."

**Summary is generated from context, not from ground truth.** When an agent says "I wrote a test that covers edge cases," it generated that summary from its own context — from the code it thinks it wrote. If its implementation is wrong, its summary of that implementation is likely also wrong. The summary is not independently checked against reality.

---

## The verification loop pattern

1. Give the agent a clear task with explicit stop conditions.
2. Agent executes and reports completion.
3. YOU verify — read the actual files, run the actual tests, check actual state.
4. If verification passes: mark the task complete.
5. If verification fails: report the specific failure to the agent with exact location and expectation.
6. Do not mark complete until verification passes — agent saying "done" is not sufficient.

```
Human: implement GetAll handler
Agent: done — I implemented GetAll in internal/handler/task.go
Human: [runs go build ./...] — build fails, file doesn't exist
Human: The file internal/handler/task.go was not created. Check and implement.
Agent: done — I created the file with GetAll
Human: [runs go build ./...] — build passes
Human: [runs go test ./...] — tests pass
Human: Task complete.
```

Step 3 is the step developers skip. It is also the step that prevents bad code from accumulating in the codebase.

---

## Hallucination recovery

**What hallucination looks like in practice:**

- Agent confirms it created a file. File doesn't exist.
- Agent confirms it added a validation check. The check is not in the code.
- Agent confirms tests pass. Tests haven't been run — tests fail.
- Agent says "I updated CLAUDE.md." CLAUDE.md is unchanged.

**Recovery — critical principle: do not argue with the agent.**

Saying "But you said you created the file — why didn't you?" does not help. The agent cannot self-correct through argument. It will generate a plausible-sounding explanation that may itself be hallucinated.

**Recovery steps:**

1. Identify the specific hallucination: "The file internal/handler/task.go does not exist."
2. Close the current context or start a fresh one.
3. Ground the new context in verifiable facts: "Read internal/handler/task.go — it does not exist. Implement it."
4. Use the file system, not the agent's memory, as the source of truth.

**Prevention:**

Ground the agent in specific files before asking it to implement. "Read internal/store/store.go first, then implement GetAll in internal/handler/task.go." Reading the file grounds Claude in actual current state — it cannot hallucinate a file it just read.

Executor agents read `docs/plans/<phase>-plan.md` (ground truth for the task) before acting, and their output is verified via git commits (ground truth for completion).

---

## Practical verification techniques

**File existence check:**
```bash
ls -la internal/handler/task.go
```

Does the file exist? If the agent said it created it and it doesn't exist: hallucination confirmed.

**Content check:**
```bash
cat internal/handler/task.go
```

Does the file content match what was specified? Is the function signature correct? Are the validation rules present? Check specific acceptance criteria from the SPEC.

**Build check:**
```bash
go build ./...
```

A passing build confirms no syntax errors, no missing imports, no type mismatches. It does not confirm correct behavior.

**Test check:**
```bash
go test ./...
```

Passing tests confirm behavior matches the test expectations. It does not confirm the tests themselves are correct (tests can be wrong).

**Behavior check:**
```bash
# Start the server
go run . &

# Test POST /tasks — expect 201
curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}' \
  http://localhost:8080/tasks

# Test POST /tasks — missing title, expect 400
curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8080/tasks
```

A passing behavior check confirms the endpoint returns the expected HTTP status codes and response bodies. This is the highest confidence verification.

**Verification hierarchy:** behavior check > test check > build check > content check > file existence. Each level catches what the level below missed. Run them in order, bottom to top.

---

## The "trust but verify" workflow in practice

After each agent task:

| Check | Command | Pass condition |
|-------|---------|---------------|
| File exists | `ls -la <file>` | File is present |
| Content correct | Read the file | Key functions, signatures, logic match SPEC |
| Builds | `go build ./...` | Zero errors |
| Tests pass | `go test ./...` | Zero failures |
| Behavior correct | curl commands | Status codes match SPEC |

You do not need to run all five for every task. Choose based on risk:
- Quick fix: build + test is sufficient.
- New handler: all five.
- Documentation update: content check only.
- Refactor: build + test + behavior check.

The rule: the verification level should match the blast radius of the task.

---

## Common verification failures and responses

| What you find | What happened | Response |
|---------------|---------------|---------|
| File doesn't exist | Agent hallucinated creation | "File X doesn't exist. Read the directory, then create it." |
| Wrong function signature | Agent used wrong interface | "The function signature is wrong. Read internal/store/store.go for the correct interface." |
| Build fails with type error | Agent made a type assumption | Report exact error: "go build fails: ./internal/handler/task.go:47: cannot use string as Task" |
| Tests fail | Implementation doesn't match spec | Report exact failure: "TestGetAll fails: expected []Task, got nil. GetAll returns nil instead of empty slice." |
| Wrong status code | Handler missing WriteHeader call | "POST /tasks returns 200, expected 201. GetTasks returns 404, expected 200." |

Specificity matters. "Your code is wrong" generates a generic response. "TestGetAll fails at line 47: expected status 200, got 404" generates a targeted fix.

---

## Checklist

- [ ] I never mark a task complete based solely on the agent's summary.
- [ ] After every agent task: I check that changed files actually exist and contain correct content.
- [ ] After every agent task involving code: I run go build ./...
- [ ] After every agent task involving a handler: I run go test ./...
- [ ] I know how to recover from hallucination: fresh context, grounded in file system state.
- [ ] I report specific failures to agents: file + line + expected + actual.
- [ ] I do not argue with agents about what they did — I verify with the file system.
