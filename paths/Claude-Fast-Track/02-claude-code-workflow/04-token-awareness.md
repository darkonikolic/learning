# Token awareness

Tokens are the unit of cost and the unit of quality. More tokens in context costs more money. More irrelevant tokens in context produces worse answers. These two effects compound.

Token awareness is not about being cheap. It is about recognizing that context efficiency and response quality are the same optimization target.

---

## What tokens are

Every word, symbol, and piece of code is broken into tokens. Roughly:
- 1 token ≈ 4 characters of English text
- 1 token ≈ 3 characters of code (more punctuation)
- 100 lines of Go ≈ 800–1200 tokens
- A full CLAUDE.md at 200 lines ≈ 1500–2000 tokens

Tokens count in both directions: input (everything in context) and output (Claude's response). You pay for both. Quality degrades as input tokens fill with noise.

---

## Context window limits and what happens when you hit them

| Model class | Approximate limit | What happens at limit |
|---|---|---|
| Claude Sonnet | ~200k tokens | Oldest context dropped or error |
| Claude Haiku | ~200k tokens | Same |
| Claude Opus | ~200k tokens | Same |

Hitting the limit is not an error you see clearly. The model starts truncating or compressing older context silently. You notice it as: Claude "forgetting" decisions from earlier in the session, responses that reference the wrong version of a file you edited, plans that contradict earlier constraints.

Prevention is better than detection.

---

## /compact: what it does, when to use it, what you lose

`/compact` compresses the session history into a summary and resets the active context to that summary plus the most recent turns.

| Aspect | Detail |
|---|---|
| What it preserves | Key decisions, file states, current task summary |
| What it loses | Exact wording of earlier turns, intermediate reasoning steps, code snippets from compressed turns |
| When to use it | Before switching to a new sub-problem, after a long debugging spiral, when context feels stale |
| When NOT to use it | Mid-task where the compressed reasoning was load-bearing — you'll lose the thread |
| Command | `/compact` in the chat input |

After `/compact`, verify that Claude still has the core plan and constraints. Send a brief re-anchor: "Continuing from the plan in docs/plans/task-api.md. We've completed steps 1-2. Starting step 3: write the handler."

---

## Prompt caching: what it is and when it saves cost

Prompt caching is an Anthropic infrastructure feature, not something you configure. Claude caches repeated prompt prefixes for 5 minutes. If you send the same large context prefix twice within that window, the second call is cheaper.

In practice this means:
- CLAUDE.md (large, stable, always loaded) gets cached after the first session call — repeated requests in the same session hit the cache.
- Files you read repeatedly in the same session benefit from caching.
- Long system prompts from skills are cached after first invocation.

You cannot force cache hits. You can make caching more likely by keeping your CLAUDE.md and rule files stable (not editing them mid-session) and by re-reading the same files rather than pasting fresh copies.

Practical benefit: in a session where you /read store.go multiple times, the second and subsequent reads cost roughly 10% of the first read's input tokens.

---

## Strategies for token efficiency

### 1. Read only what you need

| Pattern | Token cost | Signal quality |
|---|---|---|
| Paste entire project | 8000+ tokens | Low — noise dominates |
| Read two relevant files | 1200 tokens | High |
| Paste one relevant function | 200 tokens | Highest |

For the task-api: to write the POST /tasks handler, you need the Task struct and the Store interface signature. You do not need main.go, the test files, or go.mod.

### 2. Summarize before appending

When you need to carry forward a large piece of previous analysis, summarize it rather than appending the raw output. 

Bad: append a 400-token code block Claude produced earlier because you want it to stay "in scope."

Good: "The handler in internal/handlers/tasks.go from step 2 uses AddTask(ctx, task) and returns the stored task. Continue from that interface."

### 3. Use agents to isolate expensive tasks

Long-running analysis tasks (read all files and find inconsistencies) should run as isolated sub-agents, not inline in your main session. The sub-agent's context is separate — it doesn't pollute your working context.

This is an advanced pattern, but the principle applies at any level: isolate expensive exploration from your implementation session.

### 4. /compact before switching sub-problems

Every time you finish a distinct sub-problem and move to the next, run `/compact`. The completed sub-problem's context is now noise for the next one.

Sub-problem sequence for task-api:
1. Set up project structure and store — `/compact`
2. Write POST /tasks handler — `/compact`
3. Write GET /tasks handler — `/compact`
4. Write PATCH /tasks/:id/complete — done

Each compaction keeps the session clean and the cost bounded.

---

## Tracking token usage

Claude Code shows token usage in the session footer. Check it:
- After loading large files
- Before a long generation request
- When responses start feeling unfocused

If you're over 50k tokens in a session that should have used 10k, you have a context pollution problem. Use `/compact` or restart.

There is no built-in budget alert. You set the discipline yourself.

---

## When NOT to /compact

/compact destroys detail from compressed turns. Do not run it when:

- You are mid-task and the intermediate reasoning (Claude explaining what it's about to do, the specific error message it's debugging) is part of the active work.
- You haven't yet written the plan to disk — compacting before saving the plan to a file loses the plan.
- The current turn is the first in a session — nothing to compact.
- You're in a debugging spiral and the error context is still needed.

The rule: save artifacts to disk before compacting. If the plan is in chat only, write it to docs/plans/ before running /compact.

---

## Token cost by operation type (rough estimates)

| Operation | Input tokens | Output tokens | Notes |
|---|---|---|---|
| Session opener with good framing | 100–300 | 50–200 | Cheap — invest here |
| /plan with 5-step plan | 300–500 | 400–800 | One-time cost |
| Read a 200-line Go file | 1500 | 0 | Use /read, not paste |
| Generate a 100-line handler | 500 | 800 | Targeted |
| Paste whole project tree | 5000–15000 | Variable | Avoid |
| /compact on 50-turn session | N/A | 300–500 | Saves future costs |

---

## Checklist

- [ ] I know approximately how many tokens are in my current context.
- [ ] I am reading specific functions, not whole files.
- [ ] I run /compact before switching sub-problems.
- [ ] I have saved the plan to disk before running /compact.
- [ ] I am not pasting the same file content twice — I use /read and trust caching.
- [ ] I summarize large previous outputs rather than re-appending them.
- [ ] I check the token counter when responses feel unfocused.
- [ ] I do not run /compact mid-task where the thread would break.
