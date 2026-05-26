# Drift detection

Drift is always a surprise — that is what makes it drift. You did not plan for the implementation to diverge from the SPEC. Knowing when drift is likely and having a procedure to detect it systematically turns a surprise into a routine check.

---

## When drift is most likely

These are ordered by frequency. Check after any of these events before proceeding.

**After a long execute session (wave 3+)**

Multi-wave execute sessions are the highest-risk scenario. Wave 1 and wave 2 implement the primary behavior — the core is close to the SPEC. Wave 3 is where agents "complete" the feature by filling in perceived gaps. The gaps they fill may not be in your SPEC. They may be reasonable improvements. They may also be scope additions that break a constraint.

Signal: any file touched in wave 3 that was not mentioned in PLAN.md is a potential drift source.

**After a bug fix touching SPEC-covered behavior**

A bug fix changes code. If the bug was in behavior the SPEC describes, the SPEC may now describe the bug. Check: does the SPEC acceptance criterion describe the fixed behavior or the old behavior?

**After a refactor**

A rename, a package restructure, a type change. Internal changes often have external consequences. A field renamed from `created_at` to `createdAt` in the domain package propagates to the JSON response. The SPEC says `created_at`. The response now returns `createdAt`. Drift.

**After merging from another branch**

Another developer's implementation may have modified behavior your SPEC describes. The merge commit has no knowledge of your SPEC. Review changed files against SPEC acceptance criteria after every non-trivial merge.

**After /compact**

Claude's context was reset to a summary. Its next implementation turn is from a compressed version of the conversation — not the full SPEC. The file reference (`docs/specs/get-tasks.md`) survives if you include it in the next message. But if you do not reference it explicitly, Claude implements from the summary, and subtle SPEC details drop out.

**After execute-phase with --gaps-only**

A partial re-run implements only tasks that were previously skipped. Partial implementations can produce partial behavior — behavior that satisfies some acceptance criteria but not others, creating a mixed state that is harder to reason about than full drift.

---

## Manual drift detection procedure

Run this procedure any time drift is suspected. It is also the standard post-execute check.

**Step 1: open SPEC — list all acceptance criteria**

Write them out in a working document or text file, not in your head. You need to check each one systematically without skipping.

**Step 2: for each criterion, run its verification**

Use the verification mapping from `10-spec-runtime/01-executable-spec-thinking.md`. If the criterion has no verification command, that is its own problem — write one before proceeding.

**Step 3: record results**

| Acceptance criterion | Verification command | Result |
|---------------------|---------------------|--------|
| GET /tasks returns 200 | `curl -o/dev/null -w "%{http_code}" localhost:8080/tasks` | PASS |
| Empty list returns [] | Fresh server: `curl localhost:8080/tasks` | PASS |
| Tasks in creation order | POST A, POST B, jq `.[0].title` | FAIL |
| done is boolean | `jq '.[0].done | type'` | PASS |
| Content-Type: application/json | `curl -sI | grep content-type` | PASS |

Each FAIL is a candidate drift location.

**Step 4: check for excess behavior**

Read the implementation files. Look for behavior not described in the SPEC:
- HTTP routes not in the SPEC
- Response fields not in the SPEC
- Error responses not described in the SPEC
- Query parameters not in the SPEC

Excess behavior is not automatically wrong. It may be an undocumented feature (add to SPEC as evolution) or a scope addition (remove from code). The question is whether it was intentional.

**Step 5: classify each finding**

For each FAIL and each excess behavior item:
- Code right, SPEC wrong → spec evolution (update SPEC)
- SPEC right, code wrong → spec violation (fix code)
- Both wrong → rewrite criterion from problem statement

---

## Automated drift signals

These are indicators that drift may have occurred. They do not prove drift — they tell you where to look.

**Tests that previously passed now fail**

Behavior changed. Either the change was intentional (update SPEC) or a regression (fix code). Do not ignore a newly failing test.

**New code paths with no SPEC section**

A function was added with no corresponding SPEC acceptance criterion. Is this behavior intentional? If yes: add to SPEC. If no: remove from code.

**STATE.md says "completed" but verification fails items**

The phase was marked complete, but verification fails. The most common cause: verification was not run after execute, only after a partial implementation. Run full verification now.

**Coverage gaps from test-to-spec mapping**

A gap means an acceptance criterion has no corresponding test. This does not prove the behavior is wrong — but it means the behavior has no automated verification. The behavior could drift in the next session without any test catching it.

---

## Drift detection checks

| Check | What it checks | When to use |
|-------|---------------|-------------|
| Acceptance criterion verification | Acceptance items vs current behavior | After every execute session |
| Test-to-SPEC coverage mapping | Test coverage vs SPEC acceptance criteria | After execute, before ship |
| Security review | Security threat mitigations vs implementation | Before ship on any API |
| Code review | Code quality vs PLAN.md intent | Before PR |

The acceptance criterion verification is interactive — walk through each acceptance item and confirm the behavior. Use it for quick post-execute sanity checks.

The test-to-SPEC coverage mapping is systematic — check which criteria have corresponding tests and which do not. Use it for thorough pre-ship verification.

Do not skip both. They check different things: one checks runtime behavior, the other checks artifact coverage.

---

## Drift triage — three cases

When drift is confirmed, apply the three-case decision before making any change.

**Case 1: code is correct, SPEC is outdated**

The code behavior is what you want. The SPEC was written before the implementation revealed something, and the implementation took a better path.

Process: update SPEC. Write one sentence explaining why the behavior changed ("evolved to return updated task body instead of 204 because client integration is simpler"). Mark it as spec evolution in the commit message.

**Case 2: SPEC is correct, code has drifted**

The SPEC describes intended behavior. The implementation deviated without intent.

Process: fix the code. Re-run verification. Do not update the SPEC — the SPEC is correct.

**Case 3: both are wrong**

The acceptance criterion is ambiguous enough that both the SPEC description and the implementation behavior are defensible interpretations. Neither is clearly right.

Process: return to the Problem and Goal sections of the SPEC. Ask: what behavior actually solves the problem? Rewrite the criterion to be unambiguous. Then fix code or SPEC to match the rewritten criterion.

This case is the least common but the most disorienting. It usually means the original acceptance criterion was written too quickly. "Tasks returned in order" is ambiguous — ascending or descending? By creation time or by title? Rewrite: "Tasks returned in ascending creation time order — oldest first at index 0."

---

## Drift severity

Not all drift is equal. Triage before deciding how urgently to resolve.

| Severity | Definition | Example | Action |
|----------|-----------|---------|--------|
| Critical | Security or data integrity behavior differs from SPEC | Auth bypass, data corruption | Fix immediately, do not ship |
| High | Acceptance criterion fails on a deployed or shippable feature | POST /tasks returns 200 instead of 201 | Fix before ship |
| Medium | Excess behavior not in SPEC but not harmful | Extra field in response, extra query param | Document as evolution or remove |
| Low | Internal implementation strategy differs from SPEC strategy section | Used a slice instead of described linked list | Log in SPEC, no immediate action |

For task-api (no auth, no security model, no data persistence), critical severity drift does not apply. High severity is the common case. Medium is the most frequent outcome of long execute sessions.

Medium drift deserves a decision, not just a note. "Extra field in response" — is that field going to be in future SPECs? If yes: add it to the current SPEC as spec evolution and set a constraint that it must be maintained. If no: remove it before ship. An undocumented field that stays in the response becomes load-bearing for API consumers.

---

## Drift in a live scenario — worked example for task-api

Post-execute state after execute-phase 3 (PATCH /tasks/:id/complete):

Running verification:

```bash
# Criterion: 200 on valid id
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/abc123/complete
# Actual: 404 — task doesn't exist yet, this is the wrong test setup. Not drift, test error.

# Create a task first
ID=$(curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" \
  -d '{"title":"test"}' | jq -r '.id')

# Criterion: 200 on valid id
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/$ID/complete
# Actual: 200. PASS.

# Criterion: done field is true after complete
curl -s localhost:8080/tasks | jq '.[0].done'
# Actual: true. PASS.

# Criterion: idempotent — second PATCH returns same 200
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/$ID/complete
# Actual: 200. PASS.

# Criterion: 404 on unknown id
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/nonexistent/complete
# Actual: 404. PASS.

# Criterion: response body contains updated task
curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq '.done'
# Actual: null — response body is empty. FAIL.
```

One FAIL: response body is empty, but the SPEC says "returns updated task body with done=true".

Drift triage: SPEC says return updated task. Code returns empty body. SPEC is correct — the decision was documented in the Tradeoff section ("return updated task, not 204, so client doesn't need to refetch"). Code is wrong.

Fix: handler must marshal and return the updated task. Re-verify criterion 5 after fix.

---

## Checklist

- [ ] I run drift detection after every execute session — not only when something seems wrong
- [ ] I check for excess behavior (implementation features not in SPEC) not just failing criteria
- [ ] I apply the three-case decision (code right / SPEC right / both wrong) before making changes
- [ ] Drift severity is assessed — critical and high are fixed before ship, medium gets a decision
- [ ] Acceptance criterion verification is in my post-execute routine
- [ ] Test-to-SPEC coverage check is in my pre-ship routine
- [ ] I can describe the difference between a FAIL caused by a test setup error and FAIL caused by drift
