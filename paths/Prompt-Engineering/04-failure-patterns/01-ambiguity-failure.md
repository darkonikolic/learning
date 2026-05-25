# Ambiguity Failure

## Detection signals

- Output is coherent, compiles, passes a surface read — but answers a different question than you meant
- The implementation is internally consistent with *an* interpretation of your goal, just not yours
- No error; the AI was not wrong — it was *precise about the wrong thing*
- You find yourself saying "that's not what I meant" rather than "that doesn't work"

---

## Why it happens

A goal statement that permits two distinct implementations is ambiguous. The model picks one — consistently and confidently — which makes the failure hard to spot until you run it against real requirements.

Classic ambiguous statement: **"make tasks searchable"**

Valid interpretations:
- Search by title, case-insensitive substring match
- Search by numeric task ID, exact match
- Full-text search across title + description
- Filter by tag or status (also "searching" by some definitions)

The model commits to one of these. The code it produces is correct for that interpretation.

---

## Examples: ambiguous vs unambiguous

| Ambiguous | Unambiguous |
|-----------|-------------|
| `make tasks searchable` | `add GET /tasks?q= that returns tasks whose title contains q as a case-insensitive substring` |
| `improve error handling` | `return 400 with JSON {"error": "..."} for all validation failures; never return 500 for input errors` |
| `cache the results` | `cache the response of GET /tasks in memory for 60 seconds; invalidate on any POST /tasks` |
| `make the API faster` | `reduce p99 latency of GET /tasks below 50ms; do not change the response shape` |
| `add authentication` | `add Bearer token middleware that rejects requests without a valid token with 401; no login endpoint yet` |

---

## Recovery procedure

Do not ask "why did you do X?" — that produces a justification for the wrong implementation.

1. Stop. Do not build on the wrong output.
2. Restate the goal as a **single sentence** with no OR-paths.
3. Add one concrete example of correct output (a sample request + expected response, or a test case).
4. Re-prompt from the last known-good state.

```
# Recovery prompt structure

Task: [single unambiguous sentence]

Example of correct output:
  Input:  GET /tasks?q=deploy
  Output: 200 {"tasks": [{"id": 3, "title": "Deploy to staging"}]}
  (partial match, case-insensitive, title only)

Implement this. Do not add search to any other field.
```

---

## Prevention

Before submitting any goal statement, ask:

> "What are the two most different ways to implement this?"

If two valid implementations exist, the goal is ambiguous. Collapse the ambiguity before prompting.

Apply this to the four most common ambiguity sources:

1. **Scope** — which fields, which endpoints, which layers?
2. **Match semantics** — exact, prefix, substring, fuzzy?
3. **Error behavior** — what happens when input is missing, malformed, out of range?
4. **Side effects** — does this operation mutate state, trigger events, invalidate cache?

Write the constraint on each dimension before writing the goal.

```
# Prevention template

Goal: [verb] [noun] [scope]
Match: [exact | prefix | substring | none applicable]
On error: [return X | panic | ignore]
Side effects: [none | invalidate Y | emit event Z]
```

---

## Lab: ambiguity audit

Take any prompt you've written this week. Run the two-interpretation test.

For each prompt, write:
- Interpretation A (what you meant)
- Interpretation B (what a reasonable model might also do)

If you cannot construct Interpretation B, the prompt is unambiguous. If you can, rewrite before running.

---

## Checklist

- [ ] Goal restated as a single sentence with no OR-paths
- [ ] At least one concrete example of correct output included
- [ ] Scope constrained: which fields / endpoints / modules
- [ ] Match semantics explicit when any search/filter/lookup is involved
- [ ] Error behavior specified
- [ ] Two-interpretation test applied and passed
- [ ] Not building on output until interpretation is confirmed correct
