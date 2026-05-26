# Permission model and trust

Permissions define the boundaries of what an agent can do autonomously. Trust boundaries define where agent autonomy ends and human judgment begins. Together they determine the blast radius of any agent operation.

---

## Least privilege principle

Give an agent only the permissions it needs for its specific task — no more.

This principle comes from security engineering and applies directly to AI agents. An agent with `Bash(*:*)` (all bash commands) that only needs to run tests is over-privileged. If it hallucinates, it can run destructive commands. An agent with `Bash(go test:*)` that only needs to run tests is correctly privileged.

**Applied to Claude Code settings.json:**

Over-privileged (avoid):
```json
"allow": ["Bash(*:*)"]
```

Correctly privileged (prefer):
```json
"allow": [
  "Bash(go test ./...)",
  "Bash(go build ./...)",
  "Bash(go vet ./...)"
]
```

The correctly-privileged version allows exactly what the agent needs. If the agent tries to run `rm -rf ./` (accidental or hallucinated), it is blocked because that pattern is not in the allow list.

**Applied to MCP servers:**

Over-privileged (avoid):
```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you"]
```

Correctly privileged (prefer):
```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you/Documents/project-refs"]
```

The filesystem server only accesses the specific directory it needs. It cannot read your home directory, SSH keys, or other projects.

---

## Trust boundaries

A trust boundary is the line between what an agent can do autonomously and what requires escalation to a human.

Trust boundaries in Claude Code:

| Action | Position | Reason |
|--------|----------|--------|
| Read source files | Inside boundary | Necessary, read-only, zero blast radius |
| Run tests | Inside boundary | Idempotent, local, reversible by re-running |
| Run build | Inside boundary | Local, reversible |
| Git status / diff / log | Inside boundary | Read-only |
| Create/edit files | At boundary — confirm | Changes disk state, but recoverable via git |
| Git commit | At boundary — confirm | Writes history, but local until push |
| Git push | Outside boundary | Affects remote, affects team, hard to undo |
| Database mutations | Outside boundary | May affect production, hard to undo |
| `rm -rf` | Outside boundary — deny | Irreversible, high blast radius |
| Deploy to production | Outside boundary — deny | Affects users, requires deliberate action |

The boundary is not fixed — it is a design decision. A team that runs in a fully isolated sandbox with automatic rollback can push the boundary further inside (git push may be inside the boundary). A team working directly on production infrastructure should pull the boundary further outside.

For task-api: the boundary is conservative. Only read operations and local non-destructive operations are inside the boundary.

---

## Blast radius

Blast radius is the scope of potential damage from an agent action going wrong. It is a useful mental model for evaluating whether an action belongs inside or outside the trust boundary.

**Low blast radius:** action affects only the current session, the current file, or is immediately reversible.
- Running tests: blast radius = test output. Zero permanent effect.
- Editing a file: blast radius = one file. Reversible via `git checkout`.
- Creating a file: blast radius = one file. Deletable.

**Medium blast radius:** action affects multiple files or requires deliberate work to undo.
- Git commit: blast radius = the commit. Revertable, but requires a new commit.
- Refactoring many files: blast radius = all affected files. Reversible via `git reset`.

**High blast radius:** action affects remote state, other developers, users, or is irreversible.
- Git push: blast radius = remote branch, all teammates who have pulled.
- Production deployment: blast radius = all users of the system.
- `rm -rf`: blast radius = deleted files, no undo.
- Database mutation on production: blast radius = all affected data.

**Minimizing blast radius:**

Use worktree isolation for risky agent operations. A git worktree creates a separate working directory with its own branch. Changes made in the worktree don't affect your main working directory. If the agent makes a mess, you delete the worktree.

```bash
git worktree add ../task-api-agent-branch feature/get-handler
# Run agent in task-api-agent-branch/
# Review changes
# Merge if good, delete worktree if bad
git worktree remove ../task-api-agent-branch
```

Claude Code can execution stages in worktrees, providing natural blast radius containment.

---

## Tool-level vs operation-level permissions

**Tool-level permission (too broad):**
```json
"allow": ["Bash(git:*)"]
```

This allows all git commands: `git push`, `git reset --hard`, `git push --force`. Too broad for any agent that doesn't need all git operations.

**Operation-level permission (correct):**
```json
"allow": [
  "Bash(git status)",
  "Bash(git diff *)",
  "Bash(git log *)"
],
"deny": [
  "Bash(git push *)",
  "Bash(git reset --hard *)"
]
```

This allows exactly the read operations needed. Push and destructive operations are denied.

The principle: always prefer operation-level over tool-level. The extra specificity has no runtime cost. It has significant safety value.

---

## Permission escalation pattern

The safe path to giving an agent the permissions it needs:

1. **Start with read-only.** Allow Read permissions and read-only Bash commands (status, diff, log). No write permissions.
2. **Add write permissions incrementally.** When the agent demonstrably needs to write files, add Edit and Write. Verify the agent uses them correctly.
3. **Add execution permissions last.** When write permissions are working correctly, add Bash execution permissions for specific commands.
4. **Never grant destructive permissions without an explicit HITL gate.** `git push`, `rm -rf`, database mutations — these are in the deny list until you explicitly decide otherwise and put a human gate in front of them.

The escalation pattern is more work upfront and less work in incident recovery. The alternative (grant all permissions immediately) is less work upfront and potentially a lot of work in incident recovery.

---

## Trust but don't verify (anti-pattern)

The failure mode: granting permissions and trusting the agent will use them correctly without verification.

Example:
- Agent has `Edit(./**)` permission.
- Agent edits 15 files.
- You trust the agent's summary: "I updated the handler and the tests."
- Actual result: agent edited the handler, broke the store interface, "updated" the tests to match the broken implementation, and the test suite now passes by testing wrong behavior.

The agent was not lying. It described what it did. What it did was incorrect. The permission model let it make those changes without review.

Fix: permissions control what the agent CAN do. Your review controls what it DOES. These are separate concerns. Never skip review because permissions are correctly set.

---

## Checklist

- [ ] I can explain least privilege in my own words.
- [ ] My settings.json uses operation-level permissions, not tool-level.
- [ ] I can identify the blast radius of any agent action before granting permission.
- [ ] Trust boundary in my settings.json: push and destructive ops are in deny.
- [ ] I know the permission escalation pattern: read-only first, write second, execute third.
- [ ] I understand that permissions control capability, not correctness — review is always required.
