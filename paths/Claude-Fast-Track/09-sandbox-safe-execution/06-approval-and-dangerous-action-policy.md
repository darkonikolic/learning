# Approval and dangerous action policy

Claude proposes. Humans approve. Execution happens after approval. This sequence is not optional for dangerous actions — it is the policy. Automating the approval step is automating the risk.

---

## What counts as a dangerous action

Dangerous actions share one property: they are difficult or impossible to reverse cleanly after execution. The test is not "did this cause harm?" — by then it is too late. The test is "if this goes wrong, can I fully undo it?"

| Category | Examples | Reversible? |
|----------|---------|------------|
| Destructive file operations | `rm -rf`, overwrite without backup | No — unless git-tracked |
| Irreversible git operations | `git push --force`, `git reset --hard`, `git branch -D` | No — force push rewrites remote history |
| Database modifications | `DROP TABLE`, `UPDATE` without `WHERE`, `TRUNCATE` | No — unless backup exists |
| External side effects | Sending emails, triggering webhooks, API calls with mutations | No |
| Secret-adjacent | Reading `.env`, printing `env`, echoing `$SECRET_KEY` | Exposure cannot be reversed |
| Infrastructure changes | `terraform apply`, `kubectl delete`, `helm upgrade` | Partial — depends on state |
| Dependency updates | `go get`, package upgrades in lock files | Yes — via git revert |

The last row is reversible and does not require special approval. The others do.

---

## The escalation ladder

Every dangerous action follows the same ladder:

1. **Proposal** — Claude states what it intends to do and shows the exact command or change
2. **Review** — you read the proposal; you understand what will execute
3. **Approval** — you explicitly confirm; Claude proceeds
4. **Execution** — the action runs
5. **Verification** — you confirm the outcome matches the intent

If you skip step 2 (review without reading), step 3 is meaningless. Approving without reading is the habit that leads to incidents.

If Claude detects a dangerous action it cannot safely propose (e.g., the action was implicit in the task description), it should stop and ask before attempting. A Claude session that silently executes `git push --force` without surfacing a confirmation is behaving incorrectly.

---

## Claude Code's built-in approval gates

Claude Code pauses and requires explicit confirmation for:

- Any `git push`
- File deletion operations
- Commands matching patterns in the deny list
- Commands Claude classifies as destructive based on its own heuristics

These built-in gates are a safety net, not the primary policy. Do not rely on them exclusively. The primary policy is the deny list in `settings.json` and your own review habits.

---

## Custom approval policy via hooks

Pre-tool hooks let you intercept Bash calls before execution. A hook can log, validate, or block:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/you/projects/task-api/.claude/hooks/check-dangerous.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
# .claude/hooks/check-dangerous.sh
#!/bin/bash
# Called before every Bash tool execution
# CLAUDE_TOOL_INPUT contains the command Claude wants to run
# Exit 0: allow  Exit non-zero: block

COMMAND="$CLAUDE_TOOL_INPUT"

# Block irreversible git operations
if echo "$COMMAND" | grep -qE 'git push --force|git reset --hard|git branch -D'; then
    echo "BLOCKED: Irreversible git operation requires manual execution" >&2
    exit 1
fi

# Block rm -rf
if echo "$COMMAND" | grep -qE 'rm -rf'; then
    echo "BLOCKED: rm -rf requires manual execution" >&2
    exit 1
fi

# Allow everything else
exit 0
```

Make the script executable:
```bash
chmod +x .claude/hooks/check-dangerous.sh
```

The hook runs synchronously. If it exits non-zero, Claude's Bash tool call is blocked. Claude receives the stderr output as an error message and must find an alternative approach or report the blocker.

---

## The propose-then-execute pattern

For multi-step destructive operations, require Claude to propose the full sequence before executing any of it:

```
Before executing any of the following steps, show me the complete list of commands
you intend to run, in order. Do not execute until I say "approved."
```

Claude's response to this should be a numbered list of exact commands with brief explanations. Review the complete list. If any command concerns you, ask Claude to explain it or replace it with a safer alternative.

Only after reviewing the full sequence: "approved, proceed in order."

This pattern is especially important for:
- Database migrations (show the SQL before running it)
- Terraform plans (show the plan before applying)
- Multi-file refactors (show the file list and diff summary before touching anything)
- Deployment sequences (show the rollout order before starting)

---

## Approval anti-patterns

| Anti-pattern | Why it's dangerous |
|-------------|-------------------|
| Auto-approving all confirmations | Defeats the safety mechanism entirely |
| Approving without reading the proposed command | Approval becomes meaningless |
| Setting automation to skip all confirmations | The automation now has the authority you were supposed to retain |
| "Just do it, I trust you" | Trust is not a substitute for review on irreversible actions |
| Approving at pace (quickly clicking through multiple confirmations) | Each confirmation deserves the same attention |
| Approving the first step without seeing the full plan | Later steps may be irreversible and harder to review mid-sequence |

The most common failure mode is approving quickly under time pressure. A dangerous action approved in two seconds is the same as a dangerous action approved in two minutes, except one of them was actually reviewed.

---

## The forbidden-class: never automate

Some actions must never appear in automated flows — not in hooks, not in CI, not in agent scripts — without explicit, synchronous human approval:

- `git push --force` to any shared branch
- Any database `DROP`, `TRUNCATE`, or mass `DELETE`/`UPDATE` without `WHERE`
- `terraform destroy` or `terraform apply` against production state
- `kubectl delete` without namespace and label scope
- Any command that sends external messages (email, Slack, webhook with mutation)
- Any command that charges money or modifies billing
- Secret rotation or revocation (irreversible for systems depending on the old secret)

For task-api, the forbidden class is short (no production, no external systems). The habit of identifying forbidden-class actions transfers directly to real projects.

---

## Dangerous action register for task-api

| Action | Risk level | Policy |
|--------|-----------|--------|
| `git push` | Medium — pushes to remote | Review diff; confirm remote branch target |
| `git push --force` | High — rewrites remote history | Blocked by deny list; manual only |
| `git reset --hard` | High — discards uncommitted work | Blocked by deny list; manual only |
| `rm -rf` | High — unrecoverable file deletion | Blocked by deny list; never automated |
| `go generate` | Medium — executes arbitrary code | Review `//go:generate` lines before running |
| `curl external-api.com` | Low-Medium — external call | Blocked by `--network none` in Docker tests |
| `go get <new-dependency>` | Low — adds dependency | Review what is added; reversible via git |
| `git branch -D` | Low-Medium — deletes branch | Confirm branch is merged or unwanted |

---

## Command classification system

Classify recurring commands before they become habits:

**SAFE** — read-only, diagnostic, no mutation:
- `git status`, `git log`, `git diff`
- `go test ./...` (with `--network none`)
- `go vet ./...`, `gofmt`
- `ls`, `find . -name '*.go'`
- `cat` on non-secret files

**NEEDS_APPROVAL** — mutates state, reversible:
- `git add`, `git commit`
- `go get` (adds dependency)
- File writes inside the project root
- `git push` (to a branch, not main, not force)

**DANGEROUS — HUMAN MUST EXECUTE** — mutates shared state or irreversible:
- `git push --force`
- `git reset --hard`
- `git push origin main` (direct push to main)
- `rm -rf`
- Any database DDL
- Any infrastructure `apply` or `destroy`

Apply this classification to Claude's tool calls. The allow/deny list in `settings.json` enforces it mechanically. The approval habit enforces it for the NEEDS_APPROVAL category.

---

## What to do when Claude proposes a dangerous action

1. Stop. Do not approve immediately.
2. Read the exact command or change being proposed.
3. Ask yourself: what is the blast radius if this goes wrong?
4. Ask Claude to explain its reasoning if the command is not obvious.
5. If the action is in the forbidden class: tell Claude the action is forbidden and ask for an alternative approach.
6. If the action is in NEEDS_APPROVAL: verify it is correct, then approve.
7. If the action is DANGEROUS — HUMAN MUST EXECUTE: tell Claude to stop; you will run it manually.

Claude receiving "stop, I will run that manually" is not a failure. It is the policy working correctly.

---

## Checklist

- [ ] I have written down which actions are forbidden-class for this project.
- [ ] `settings.json` deny list covers `rm -rf`, `git push --force`, `git reset --hard`.
- [ ] Pre-tool hook (or deny list alone) blocks the forbidden class from executing automatically.
- [ ] I know the escalation ladder: proposal → review → approval → execution → verification.
- [ ] I have practiced the propose-then-execute pattern at least once.
- [ ] I can state the difference between SAFE, NEEDS_APPROVAL, and DANGEROUS — HUMAN MUST EXECUTE.
- [ ] I have never approved a dangerous action without reading what it will do.
- [ ] I understand why "I trust Claude" is not a substitute for reviewing irreversible actions.
- [ ] The dangerous action register for task-api is written and current.
