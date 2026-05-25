# Non-Goals as Constraint

## Why non-goals outperform positive descriptions

Telling the model what to build describes a target. Telling it what not to build describes a boundary. The model stops at boundaries. It drifts toward targets.

A goal statement like "add a GET /tasks endpoint" is complete from your perspective — you know what you mean. The model fills the rest with judgment: "a GET endpoint probably needs filtering, and filtering means query params, and query params means validation, and validation means error messages, and error messages should probably follow the existing pattern in the 400 handler..." None of that was asked for. None of it was prevented.

Non-goals prevent scope creep by forcing an explicit decision. You are not relying on the model to infer the minimum viable version. You are telling it the minimum viable version is the only acceptable version.

## The rule: 3 non-goals minimum after every goal

After every goal statement, write at least 3 non-goals — the 3 things a reasonable developer would add while implementing the feature.

Pattern:
```
Goal: [what to build]

Non-goals:
- [reasonable thing someone would add — do not build]
- [reasonable thing someone would add — do not build]
- [reasonable thing someone would add — do not build]
```

Three is the floor. If you can think of four or five, write them. The cost of an unnecessary non-goal is one line of text. The cost of a missing non-goal is an LLM that rewrote your pagination logic "while it was there".

## How to identify non-goals

Ask: "What would a reasonable developer add while implementing this?"

The answer to that question is your non-goal list. Not things that are absurd or irrelevant — things that are reasonable, helpful, and completely out of scope.

A developer implementing GET /tasks would reasonably add:
- Filtering by status because tasks lists always need it
- Pagination because nobody returns unbounded lists
- Sorting because users want it
- Auth middleware because this is probably a protected resource
- A search param because it's a list endpoint

Every one of those is a non-goal for "add a basic GET /tasks endpoint that returns all tasks".

This exercise also clarifies your own thinking. If you write "no pagination" and then feel uncomfortable about it, that discomfort means you actually do need to decide on pagination — not leave it for the model to infer.

## The scope creep failure mode

The canonical failure: you ask for a feature. The model adds three others. The output is technically correct and probably useful. You accept it because it looks fine. Three days later you're debugging an interaction between the pagination it added and the cursor-based pagination your frontend already had.

The model is not being reckless. It is being helpful by the only definition it has: complete, reasonable code. "Reasonable" means "what a competent developer would do." A competent developer would add pagination. You needed to say no.

Common scope creep patterns by task type:

| Task | What the model adds without being asked |
|---|---|
| New endpoint | Auth, validation, logging, error handling beyond spec |
| Bug fix | Refactor of surrounding code, additional defensive checks |
| Add a field | Migration logic, index, cascading changes to related models |
| Refactor | Logic improvements, "while I'm here" bug fixes |
| Add a test | Tests for adjacent untested code, test helpers, fixtures |

## Example: GET /tasks endpoint

**Goal:** Add a GET /tasks endpoint that returns all tasks from the database.

**Weak prompt (no non-goals):**
```
Add a GET /tasks endpoint to the tasks API.
```

**Strong prompt (with non-goals):**
```
Add a GET /tasks endpoint to internal/handler/tasks_handler.go.

Goal: return all tasks from the database as a JSON array

Non-goals — do not implement:
- filtering by any field
- pagination or cursor logic
- sorting or ordering parameters
- authentication or authorization checks
- search functionality
- response envelope wrapping (return the array directly)

must: match the existing handler pattern in this file
must not: modify any other handler or file
```

The non-goals do not just prevent bad output — they document intent. When someone reviews this code, the non-goals tell them the simplicity was deliberate.

## Example: Add email notifications

**Goal:** Send an email when a task is marked complete.

**Non-goals:**
- Do not add email templates — use a hardcoded string
- Do not add an unsubscribe mechanism
- Do not add retry logic for failed sends
- Do not queue emails — send synchronously in the same request
- Do not add email tracking or open pixels

Without these, the model will produce a full email system with templates, a queue, retry with backoff, and a config struct for SMTP settings. All reasonable. None of it asked for.

## Claude and Cursor: where to place non-goals

Both tools read non-goals the same way — as explicit constraints. Placement matters.

**In Claude Code (single prompt or CLAUDE.md):**
Put non-goals immediately after the goal statement, before any implementation instructions. The model reads top to bottom and front-loads constraints from earlier in the prompt.

```
Goal: [what to build]

Non-goals:
- ...

Implementation:
[instructions]
```

**In Cursor (composer or inline):**
Same structure. Cursor's composer treats the full prompt as context. Put non-goals before the file-specific instructions so they apply to all files the model might touch.

If you are using a `.cursorrules` file for persistent constraints, add your project-level non-goals there: "this project does not use ORMs", "this project does not add logging inside business logic", "pagination is handled at the API gateway, not in handlers."

## Checklist

- [ ] Every goal statement followed by at least 3 non-goals
- [ ] Non-goals are things a reasonable developer would add (not absurd exclusions)
- [ ] Non-goals written as explicit "do not" statements, not as soft preferences
- [ ] Non-goals cover: related features, defensive additions, "while I'm here" improvements
- [ ] Non-goals placed before implementation instructions in the prompt
- [ ] Discomfort with a non-goal treated as a signal to make a real decision, not skip it
