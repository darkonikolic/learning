# Skills and Snippets

---

## What they are

**Skills** [Claude]
Reusable slash commands that run a defined workflow. Defined as Markdown files in `.claude/agents/` or a `skills/` directory. Invoked with `/skill-name`. The file describes a multi-step process the model follows every time.

**Snippets / Saved Prompts** [Cursor]
Saved prompt templates stored in Cursor settings (or as `.cursor/prompts/*.md` files). Inserted into chat via the prompt picker or pasted manually. Support `{{placeholder}}` syntax for variable substitution.

---

## When to extract a skill or snippet

Extract when you have written the same prompt 3 or more times with minor variations.

Signs you need extraction:
- You keep a `prompts.txt` file with blocks of text you copy-paste
- You find yourself typing "as usual, check for spec compliance, naming conventions, and error shape" repeatedly
- A teammate asks "what prompt do you use for X?" and you have to dig through history

Do not extract:
- One-off tasks where the context changes completely each time
- Tasks that require heavy customization per use (the template would have more placeholders than content)
- Exploratory prompts where you're still figuring out what you want

---

## Skill anatomy [Claude]

Every skill file follows the same structure:

```markdown
# Skill: [name]

## Trigger
/[command-name]

## Purpose
One sentence: what this skill produces.

## Inputs
- What context the model needs before starting
- File paths, references, or arguments the caller provides

## Workflow
1. Step one — what the model does first
2. Step two — conditional on step one output
3. Step three — produces the output

## Output contract
- Exactly what the skill produces (file, inline response, list, etc.)
- Format of that output
- What the caller does with it
```

---

## Snippet anatomy [Cursor]

```
# Snippet: [name]

{{context_description}}

Task: [what you want done]

Constraints:
- [constraint one]
- [constraint two]

Output format: [exactly what you expect back]
```

Cursor does not enforce this structure — it is a convention. Keep it consistent so snippets are predictable.

---

## Concrete examples

### "Review this handler for spec compliance" [Claude]

```markdown
# Skill: review-handler

## Trigger
/review-handler

## Purpose
Audit a route handler against its spec file and project constraints.

## Inputs
- Path to handler file: src/handlers/[name].js
- Path to spec file: tests/unit/[name].spec.js (must exist)

## Workflow
1. Read the spec file. Extract every acceptance criterion.
2. Read the handler implementation.
3. For each criterion: determine if the handler satisfies it. Mark PASS / FAIL / MISSING.
4. Check handler against project constraints: stdlib-only, no global state, error-shape.
5. List violations found. For each violation: quote the offending line, state the rule broken.

## Output contract
- Inline response only (no file writes)
- Format:
  CRITERIA COVERAGE
  [criterion] → PASS | FAIL | MISSING

  CONSTRAINT VIOLATIONS
  [file:line] [rule name] — [what was found]

  SUMMARY: [pass count] / [total criteria] criteria met, [n] violations
```

---

### "Write spec for this feature" [Claude]

```markdown
# Skill: write-spec

## Trigger
/write-spec

## Purpose
Generate a spec file before implementation begins.

## Inputs
- Feature description (provided by caller after invoking the skill)
- Route or module name

## Workflow
1. Ask: "Describe the feature in one sentence and name the handler/module."
2. Generate acceptance criteria from the description — behavior-first, not implementation-first.
3. Write tests/unit/[name].spec.js with one describe block per criterion.
4. Each test name is derived directly from the criterion text.
5. Test bodies contain only `expect(...).toBe(...)` stubs — no implementation.

## Output contract
- Creates tests/unit/[name].spec.js
- Does not write any src/ files
- Reports: "Spec written. [n] criteria. Ready for /review-handler after implementation."
```

---

### "Refactor this function" [Cursor]

```
# Snippet: refactor-function

Refactor the function at {{file_path}}:{{function_name}}.

Constraints:
- Do not change the function signature (inputs and outputs stay identical)
- Do not add new dependencies
- All existing tests must still pass after the refactor

Focus on: {{focus}} (e.g. "readability", "reduce nesting", "extract repeated logic")

Output: show the refactored function only. No explanation unless you changed behavior.
```

Usage: open Cursor chat, insert snippet, fill in `{{file_path}}`, `{{function_name}}`, and `{{focus}}`.

---

### "Review this file" [Cursor]

```
# Snippet: review-file

Review @{{filename}} against the project constraints in .cursorrules.

Check for:
1. Constraint violations (stdlib-only, no global state, error-shape)
2. Missing or incorrect error handling
3. Test coverage gaps (is there a corresponding spec file?)

Output format:
VIOLATIONS: [line number] [rule] — [finding]
GAPS: [what is missing]
CLEAN: [what is correct and why it matters]

Do not rewrite the file. Report only.
```

---

## When NOT to use skills

| Situation | Reason |
|---|---|
| One-off task with unique context | Skill template adds overhead without reuse benefit |
| Task where every use needs heavy customization | More placeholders than content — just write the prompt |
| Exploratory / architectural discussion | The conversation itself is the output; no contract needed |
| Learning a new codebase | Context changes too fast; premature extraction locks you into wrong assumptions |

The test: if filling in the template takes longer than writing the prompt from scratch, don't use a skill.

---

## Checklist

- [ ] Skills exist for tasks you have prompted 3+ times with minor variation
- [ ] Each skill file has trigger, purpose, inputs, workflow, and output contract sections
- [ ] Each Cursor snippet has named placeholders for variable parts
- [ ] Skills do not overlap — each one does one defined thing
- [ ] One-off tasks are not wrapped in skills
- [ ] Skill output contracts are specific: format, file path, or inline — not "responds appropriately"
- [ ] Snippets are version-controlled alongside the project (`.cursor/prompts/` or similar)
