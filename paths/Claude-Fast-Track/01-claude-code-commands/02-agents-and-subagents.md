# Agents and subagents

## What agents are in Claude Code

An agent in Claude Code is a Claude instance with a constrained configuration: a custom system prompt, a restricted tool list, an optional model override, and optional persistent memory. The main thread spawns agents to delegate bounded work.

Agents are not magic. They are Claude running with a different instruction set. The quality of an agent's output depends entirely on the quality of its configuration and the clarity of the prompt you give it.

**The main thread remains accountable.** Agents are contractors. They execute; the main thread decides whether the execution is acceptable.

---

## Agent file locations

| Scope | Path | When to use |
|-------|------|-------------|
| Project | `.claude/agents/<name>.md` | Agent relevant to this repo only |
| User | `~/.claude/agents/<name>.md` | Agent you use across all projects |

Format: Markdown with YAML frontmatter. Manage via `/agents` in session.

---

## Full agent file example

`.claude/agents/code-reviewer.md`:

```markdown
---
name: code-reviewer
description: Read-only reviewer for diffs. Invoke before merge on any change that modifies business logic.
tools: Read, Grep, Glob
model: inherit
---

You are a senior Go reviewer. Do not edit files.

For each finding provide:
- Severity: blocker | major | minor
- File and line number
- A falsifiable description of the issue (not "this looks wrong" — "this returns nil without checking the error from db.QueryRow")
- A suggested fix direction (no full rewrites)

If a behavior change has no test, mark it blocker severity.
Output a summary table at the end: severity counts and overall verdict (approve | approve-with-notes | block).
```

Key decisions in this file:
- `tools: Read, Grep, Glob` — no Write, no Bash. Cannot accidentally modify files.
- `description` tells Claude when to invoke it automatically. Be specific — vague descriptions cause spurious invocation.
- System prompt demands falsifiable findings. "Looks wrong" findings are not actionable.

---

## When Claude spawns agents automatically vs when you control it

**Automatic:** The execute-phase workflow spawns subagents per wave internally. `/batch` decomposes work and spawns agents in parallel worktrees. `/code-review` invokes a reviewer agent internally.

**Manual:** You invoke an agent explicitly by prompting "use the code-reviewer agent on the current diff" or by configuring the `agent` field in settings for a session slice.

For the structured workflow loop, you configure the agents used at each phase and verify their output.

---

## Foreground vs background agents

| Mode | Behavior | Use when |
|------|----------|----------|
| Foreground | Runs in main thread; blocks until done; result merges back immediately | Short exploration; small review; decision-dependent work |
| Background | Spawned as separate task; parent continues; check with `/tasks` | Long research; indexing; parallel audit of many files |

Background agents are powerful for parallel work. They require clear acceptance criteria and bounded file scope in the prompt — without these, you get unpredictable output with no way to evaluate it.

---

## How to write a good agent prompt — the "brief a colleague" principle

A good agent prompt answers:
1. What is the role and what can it NOT do?
2. What files or scope is it working in?
3. What does the output look like?
4. What does the parent need to verify on return?

**Bad agent prompt:**
```
Review the code and find problems.
```

**Good agent prompt:**
```
Review tasks/store.go and tasks/handler.go.
Focus on: error handling, nil pointer risks, SQL injection vectors.
Do not modify files.
For each issue: file:line, severity (blocker/major/minor), one-sentence description.
Return a bullet list then a verdict: approve | block.
```

The bad prompt produces vague findings. The good prompt produces findings the main thread can act on without follow-up questions.

---

## Parallel agents — when and how

Use parallel agents when:
- Multiple independent files need the same transformation
- You want simultaneous review and implementation on separate branches
- A large codebase needs auditing across many packages

`/batch` handles this for large structured changes — it decomposes the work, creates git worktrees, and runs agents in parallel. Requires a git repo. Review the decomposition plan before approving — blast radius is multi-file.

Manual parallelism: open multiple Claude Code sessions in separate terminals, each with a bounded task. Share context via files (STATE.md, notes/), not via chat.

---

## Trust but verify — agent says it did X does not mean X was done

Agents report their work. They can be wrong, incomplete, or misinterpret scope. Before treating an agent's output as ground truth:

- Check file:line references exist and contain what the agent claims.
- Run tests if the agent executed code changes.
- Read the diff, not just the summary.
- Check that the agent stayed within its scope (no stray edits in unrelated files).

For the code-reviewer agent specifically: read at least the blocker findings yourself. Do not auto-approve an agent's "no blockers" verdict without spot-checking two or three of its "clean" findings.

---

## Worktree isolation mode

`/batch` runs agents in git worktrees — separate directory trees checked out from the same repo. Each agent works in its own worktree; changes do not interfere. Parent merges approved worktree changes.

Use this for: large-scale refactors, applying a pattern across many files, running independent feature implementations in parallel for comparison.

Do not use this for: anything where the agents need to coordinate mid-task (they cannot see each other's worktrees).

---

## Anti-patterns

| Bad | Why | Good |
|-----|-----|------|
| Delegating understanding to an agent | You lose ownership of the decision | Understand the problem yourself; delegate execution |
| Vague agent prompts | Output is unactionable | Use the "brief a colleague" structure |
| Agent with full tool access | Agent can modify files it should only read | Minimal tool list per role |
| Trust agent summary blindly | Agents misrepresent scope or completeness | Verify file:line for critical findings |
| Many overlapping agents | Confusion about which to invoke when | Few agents, clear non-overlapping roles |
| Subagent implements without approved plan | Scope surprise on return | Plan approved by main thread; agent executes specific slice |

---

## Lab — build and use the code-reviewer agent

1. Create `.claude/agents/code-reviewer.md` with the example content above.
2. In your `task-api` directory, make a small change: add a function to `tasks/store.go` that has an obvious issue (return nil error when `db` is nil, for example).
3. In Claude Code, run: "Use the code-reviewer agent to review tasks/store.go."
4. Examine the output. Does it catch the issue? Is the finding falsifiable?
5. Compare: ask the same review question in the main thread without using the agent. Compare quality and specificity.
6. Document one finding from the agent that the main thread needs to verify directly (check file:line, confirm the issue is real).

---

## Checklist

- [ ] I created a `.claude/agents/code-reviewer.md` with read-only tools.
- [ ] I understand the difference between foreground and background agents.
- [ ] I can write an agent prompt that specifies scope, output format, and parent handoff.
- [ ] I know that `/agents` manages agent configurations in session.
- [ ] I understand that `/batch` uses worktrees for parallel agent execution.
- [ ] I have verified at least one agent finding by checking file:line myself.
- [ ] I understand that the main thread is accountable for agent output quality.
- [ ] I know how to check background agent status with `/tasks`.
