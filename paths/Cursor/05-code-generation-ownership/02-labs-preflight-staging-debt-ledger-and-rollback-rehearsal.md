# Unit 2 — Labs: generation preflight + integration audit

Select a **non-trivial** but bounded task (e.g. add idempotency key handling to a command handler stub).

## Lab 1 — Preflight contract

List **invariants** + **forbidden edits** + **verification commands** before any generation.

## Lab 2 — Staged plan

Break into **≤3** integration-safe steps with explicit checkpoint after each (tests green).

## Lab 3 — Diff narrative

After execution (human or assisted), author **commit message story** mapping each hunk to invariant.

## Lab 4 — Debt note

If expedient shortcut taken, file **`DEBT.md` entry** with trigger condition for repayment.

## Lab 5 — Rollback rehearsal

Describe exact revert / flag flip / DB forward-fix path if deployment misbehaves.

Success metric: another engineer (or future you) can **review without re-running model** and still trust intent.
