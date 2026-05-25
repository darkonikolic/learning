# Verify-work and ship

Execute-phase writes code. Verify-work proves it does what the phase said it would do. Ship gets it to mainline. The sequence is mandatory. Skipping verification creates undetected gaps between spec and implementation.

---

## `/gsd:verify-work`

Conversational UAT against the phase goal. GSD walks through each acceptance criterion from CONTEXT.md and SPEC.md, asks you to confirm pass or fail, and records the result.

This is not automated testing. Tests verify code behavior. Verify-work verifies that the code satisfies the human-readable acceptance criteria. Both are needed. They check different things.

**What it produces:** A UAT artifact stored under the phase folder (typically `UAT.md` or a verification section in STATE.md depending on GSD version). The artifact records each criterion with its pass/fail status.

**When to run:** After execute-phase, before ship. No exceptions. If you ship without a verification artifact, you have no evidence that the phase goal was met.

---

## The 1:1 rule

Every acceptance criterion in CONTEXT.md maps to exactly one verification check in verify-work. No criterion should map to zero checks (unverified). No check should exist without a criterion (untethered verification).

For task-api Phase 1:

| Acceptance criterion | Verification check |
|---------------------|-------------------|
| POST /tasks with valid body returns 201 | `curl -s -X POST localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"buy milk"}' -w '\n%{http_code}'` → 201 |
| Response includes task JSON | Response body contains `{"id":1,"title":"buy milk","done":false}` |
| Missing title returns 400 | `curl -s -X POST localhost:8080/tasks -d '{}' -w '\n%{http_code}'` → 400 |
| Empty title returns 400 | `curl -s -X POST localhost:8080/tasks -d '{"title":""}' -w '\n%{http_code}'` → 400 |
| Second task has id:2 | Create two tasks; second response has `"id":2` |

If a criterion cannot be checked with a concrete command, the criterion was not concrete enough. The issue is in CONTEXT.md, not in verify-work.

---

## What to do with FAIL items

Verify-work reveals a gap. Options are: fix it, defer it with an explicit waiver, or escalate to a follow-up command.

| Gap type | Follow-up command | When to use |
|----------|------------------|-------------|
| Tests missing for passing behavior | `/gsd:validate-phase N` or `/gsd:add-tests` | After confirm: behavior correct, coverage absent |
| Security concern discovered | `/gsd:secure-phase N` | Any phase touching input validation, external data |
| Code quality issues | `/gsd:code-review` | Implementation works but review found problems |
| Frontend rendering problems | `/gsd:ui-review` | Only for phases with UI |
| AI evaluation gaps | `/gsd:eval-review` | Only for phases with LLM calls |

**Explicit waiver:** If you decide to defer a FAIL item, record it in STATE.md:
```
Verification gap: title length validation (>200 chars) not implemented.
Waiver: deferred to Phase 1 patch — low risk for toy project.
Next action: add validation in follow-up execute before ship.
```

A waiver is not the same as ignoring the gap. The gap is recorded. The decision to proceed despite it is explicit.

---

## Verification for task-api: running the server

For verify-work to run curl checks on task-api, the server must be running. Start it in a separate terminal before verify-work begins:

```bash
# Build and run
go run main.go

# In another terminal, run verification checks:
curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"buy milk"}' | jq .

# Expected: {"id":1,"title":"buy milk","done":false}

curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{}' | jq .

# Expected: {"error":"title is required"}, status 400
```

Note the status code explicitly — `curl` does not show it by default. Add `-w '\n%{http_code}'` or check with `-o /dev/null -w '%{http_code}'`.

---

## `/gsd:pr-branch`

Before ship, create a clean branch without `.planning/` commit noise:

```
/gsd:pr-branch
```

Execute-phase commits include `.planning/` updates (STATE.md, ROADMAP.md markers). Reviewers do not need to see planning artifact history — only the code changes.

`/gsd:pr-branch` creates a new branch with only the code changes, squashing or filtering the planning artifact commits. Use this branch for the PR.

What it does:
1. Creates a new branch from the base branch (main or equivalent)
2. Cherry-picks or replays only commits that touch non-`.planning/` files
3. The result: a clean diff that reviewers can review without planning noise

When to skip: internal projects where the team also uses GSD and wants full `.planning/` history in the branch. In that case, ship directly.

---

## `/gsd:ship`

```
/gsd:ship
```

Creates the PR, optionally triggers review bots, and bridges local GSD completion to mainline merge.

**Prerequisites before running ship:**
- `/gsd:verify-work` has run and verification artifact exists in STATE.md or phase folder
- All FAIL items are either fixed or have explicit STATE.md waivers
- `/gsd:pr-branch` has run if you want a clean PR branch
- `go build ./...` passes
- `go test ./...` passes

**What ship creates:**
- Pull request on the remote (GitHub, GitLab, etc.)
- Optional: review bots if `/gsd:config --integrations` has external reviewers configured
- Commit message referencing the phase and verification artifact

---

## Do not ship anti-patterns

| Anti-pattern | Why it fails | Correct action |
|--------------|-------------|----------------|
| "Tests pass so it is verified" | Tests verify code; verify-work verifies SPEC acceptance | Run `/gsd:verify-work` |
| "It worked in my manual testing" | No artifact, not reproducible, not linked to acceptance criteria | Document in verify-work, create artifact |
| "I will do security review after merge" | Security issues in production are expensive | Run `/gsd:secure-phase N` before ship |
| "The plan changed midway, but it mostly covers the original goal" | STATE.md diverged; verification checks wrong criteria | Reconcile CONTEXT.md and rerun verify-work |
| "One acceptance criterion is failing but it is minor" | Minor gaps compound; ship with an explicit waiver or fix first | Fix or waiver in STATE.md |

---

## Ship sequence checklist

Before every `/gsd:ship`:

- [ ] `/gsd:execute-phase N` completed without mid-wave blockers
- [ ] `go build ./...` passes
- [ ] `go test ./...` passes
- [ ] `/gsd:verify-work` run — verification artifact exists
- [ ] All FAIL items: fixed or explicitly waived in STATE.md
- [ ] `/gsd:code-review` run (or decision to skip is explicit)
- [ ] STATE.md phase status reflects completed execution
- [ ] `/gsd:pr-branch` run if clean PR branch needed

---

## Checklist

- [ ] I know the difference between automated tests and verify-work.
- [ ] I can apply the 1:1 rule to match acceptance criteria to verification checks.
- [ ] I know the four follow-up commands when verify-work finds gaps.
- [ ] I know what an explicit waiver is and how to record it in STATE.md.
- [ ] I know what /gsd:pr-branch does and when to skip it.
- [ ] I would never ship without a verification artifact in STATE.md.
- [ ] I can recite the ship sequence checklist from memory.
- [ ] I understand why "tests pass" does not equal "verified against spec".
