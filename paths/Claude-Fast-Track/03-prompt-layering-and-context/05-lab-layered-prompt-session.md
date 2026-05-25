# Lab: layered prompt session

Practice using all three message layers explicitly. By the end of this lab you will have a working rule file, a minimal SPEC, and evidence that each layer does what you expect.

**Prerequisites:** task-api project exists with a CLAUDE.md from module 02. If not, create the project structure first.

---

## Step 1: Verify CLAUDE.md exists

Open a terminal in the task-api directory:
```bash
cat CLAUDE.md
```

If CLAUDE.md does not exist, create it:
```bash
mkdir -p task-api && cd task-api
```

Minimal CLAUDE.md for this lab:
```markdown
# task-api

## Stack
- Language: Go 1.22
- HTTP: stdlib net/http
- Storage: in-memory with sync.RWMutex
- External dependencies: none (stdlib only)

## Critical constraints
- Must not add external packages.
- Must validate input at handler boundary.
- Error responses: {"error": "message"}, always application/json.

## Key paths
- Handlers: internal/handler/
- Entry point: main.go

## Rules (load when relevant)
- spec-before-code: .claude/rules/spec-before-code.md
```

---

## Step 2: Create the .claude/rules/ directory

```bash
mkdir -p .claude/rules
```

Verify:
```bash
ls .claude/rules/
```

---

## Step 3: Create the spec-before-code rule file

Create `.claude/rules/spec-before-code.md`:

```markdown
---
name: spec-before-code
description: Require SPEC file on disk before writing implementation code for any feature
---

# spec-before-code

Before writing implementation code for any feature:

1. Check whether a SPEC file exists in docs/specs/<feature>.md.
2. If no SPEC exists: write the SPEC first and stop. Do not proceed to implementation.
3. If a SPEC exists: confirm the SPEC is current before implementing.
4. Do not implement without an approved SPEC on disk.

Why: implementation written without a SPEC cannot be verified against intent. The SPEC is the contract; the implementation is evidence of fulfilling the contract.

This rule applies to: new endpoints, new business logic, new validation rules.
This rule does not apply to: refactoring, bug fixes, test additions for existing behavior.
```

Verify the file exists:
```bash
cat .claude/rules/spec-before-code.md
```

---

## Step 4: Create a minimal SPEC for POST /tasks

If docs/specs/post-tasks.md does not exist, create it:
```bash
mkdir -p docs/specs
```

Create `docs/specs/post-tasks.md`:
```markdown
# SPEC: POST /tasks

## Summary
Create a new task. Returns the created task with generated ID.

## Request
- Method: POST
- Path: /tasks
- Content-Type: application/json

## Request body
- title: string, required, max 200 characters
- description: string, optional

## Response: success
- Status: 201 Created
- Body: created Task object as JSON
- Content-Type: application/json

## Response: validation failure
- Status: 400 Bad Request
- Body: {"error": "descriptive message"}

## Acceptance criteria
- [ ] Returns 201 on valid input
- [ ] Returns 400 if title is missing
- [ ] Returns 400 if title exceeds 200 characters
- [ ] Returns 400 if body is not valid JSON
- [ ] Response includes generated task ID
- [ ] Response Content-Type is application/json
```

---

## Step 5: Write a three-layer message

Open Claude Code in the task-api directory. Send this message, which uses all three layers:

```
Implement body parsing only for POST /tasks.

SPEC contract: docs/specs/post-tasks.md — the "Request body" section defines fields.
Binding acceptance criteria: items 3 and 4 only (400 on invalid body JSON, fields defined).

Constraints for this turn:
- Parse body and decode JSON only. 
- Stop before: validation logic, store calls, tests.
- Return 400 with {"error": "invalid request body"} if JSON decode fails.
- Handler location: internal/handler/task.go, CreateTask function.
- No external packages. stdlib encoding/json only.
```

Layer 1 (implicit): CLAUDE.md "stdlib only" constraint and the spec-before-code rule.
Layer 2 (explicit): `docs/specs/post-tasks.md` as ground truth.
Layer 3 (explicit): turn stops after body parsing — no validation, no store calls, no tests.

**Observe:** does Claude implement body parsing and stop, or does it continue to validation?

Expected behavior: Claude parses the body, decodes JSON, handles bad JSON with 400 — and stops. It should not add validation logic or call any store.

If Claude continues past the stop condition: the per-turn constraint layer was too weak. Add more explicit language: "STOP after JSON decode. Do not add any validation. Do not call any store method. End of this turn."

---

## Step 6: Expand scope in the second turn

Send this message, which changes only the per-turn constraints:

```
Continue from the previous step. Now add input validation.

Same SPEC contract: docs/specs/post-tasks.md — add validation for acceptance criteria 1 and 2.

Constraints for this turn:
- Add validation: title required, title max 200 chars.
- Return 400 with {"error": "title is required"} if title is empty.
- Return 400 with {"error": "title exceeds 200 characters"} if title is too long.
- Stop before: store calls, tests.
```

Observe: does Claude add validation and stop before calling the store?

The only change between turn 1 and turn 2: the per-turn constraints expanded. The SPEC contract is the same file. CLAUDE.md is still active.

---

## Step 7: Test the spec-before-code rule

Send this message to trigger the rule:

```
Implement GET /tasks. Return all tasks as a JSON array.
```

No SPEC reference. No SPEC file for GET /tasks exists.

**Expected behavior:** Claude recognizes there is no SPEC for GET /tasks, writes `docs/specs/get-tasks.md` first, and stops before implementing.

If Claude implements without a SPEC: the rule was not loaded or not followed. Check:
1. Is `.claude/rules/spec-before-code.md` in the correct location?
2. Does CLAUDE.md reference the rule?
3. Explicitly invoke the rule: "Before implementing, check the spec-before-code rule in .claude/rules/spec-before-code.md."

---

## Step 8: Note which layer caused the rule-violation response

When Claude refused to implement GET /tasks without a SPEC, which layer caused the refusal?

Answer: Layer 4 (rule file). The rule file `.claude/rules/spec-before-code.md` is the source. CLAUDE.md pointed at it. Claude loaded it because it was relevant.

If you had not written the rule file — only mentioned "require SPEC before code" in CLAUDE.md — the constraint would be in Layer 3 (project CLAUDE.md). It would still work, but it would be less detailed and harder to enforce consistently.

The rule file pattern makes enforcement:
- Detailed: the rule explains the why and the exceptions
- Separable: removing the rule file removes the constraint cleanly
- Visible: you can read the rule in isolation without parsing CLAUDE.md

---

## Verification checklist

After completing the lab:

- [ ] Rule file created at .claude/rules/spec-before-code.md with correct frontmatter.
- [ ] docs/specs/post-tasks.md exists with acceptance criteria.
- [ ] Three-layer message sent: SPEC contract reference, per-turn stop condition.
- [ ] Claude stopped after body parsing in turn 1 (no validation, no store).
- [ ] Claude added validation in turn 2 but stopped before store calls.
- [ ] Rule violation scenario tested: asked Claude to implement GET /tasks without SPEC.
- [ ] Claude refused or wrote SPEC first (rule was active).
- [ ] Identified which layer caused the refusal (Layer 4: rule file).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Claude implemented past the stop condition in turn 1 | Per-turn constraints not strong enough | Add "STOP at X. Do not proceed to Y." |
| Claude ignored the SPEC reference | SPEC file path wrong or file doesn't exist | Verify file path matches the reference |
| spec-before-code rule not triggered | Rule file not found or CLAUDE.md not referencing it | Check .claude/rules/ path, check CLAUDE.md rules section |
| Claude asked "what is in post-tasks.md?" | SPEC file exists but Claude didn't read it | Add "Read docs/specs/post-tasks.md now" to message |
| Turn 2 also stopped before store | Stop condition from turn 1 carried into session context | Re-state in turn 2: "The turn 1 stop is no longer in effect." |
