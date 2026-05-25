# Scope Signals — Reading Output Before You Accept It

## What scope signals are

A scope signal is a pattern in the output that tells you the prompt was under-constrained. You can detect them before accepting the output, before running the code, and in Claude Code — before the model finishes generating.

Recognizing scope signals is cheaper than fixing the output. Fixing under-constrained output means: reviewing code you didn't ask for, reverting changes that touched the wrong files, and debugging interactions between your code and the model's additions.

Reading output for scope signals is a skill. These are the four patterns to train on.

## Signal 1: output touches files not mentioned in the prompt

The model modified, created, or imported from a file you did not reference.

What this looks like:
- A new file appears in the diff
- An existing file outside your stated scope has changes
- The model added an import from a package you didn't mention
- A test file was created or modified when you didn't ask for tests

What it means: the model interpreted your goal as requiring more than you specified. It made a judgment call about scope. That judgment may be wrong.

What it does not mean: the changes are bad. Sometimes the model is right that another file needs to change. But "the model decided to touch it" is not the same as "you decided to touch it."

Action: stop. Identify which files were out of scope. Decide intentionally whether those changes are acceptable. If not, restart with explicit file scope constraints.

## Signal 2: output adds a feature that "makes sense" but wasn't asked

The model implemented something you didn't request because it logically follows from what you did request.

What this looks like:
- You asked for a POST endpoint, the model also added input sanitization
- You asked for a bug fix, the model also refactored the function it was in
- You asked for a new field, the model also added a getter method
- You asked for validation, the model also added error codes you haven't defined elsewhere

What it means: the model is completing what it thinks the feature should look like. It is reasoning about what belongs with the task, not what you specified.

Danger level: high. These additions are often plausible and blend in. You review the output, it looks reasonable, you accept it, and you've now committed to an error handling pattern or a sanitization behavior that you didn't evaluate.

Action: stop before the feature is accepted. Evaluate whether the addition is actually wanted. If yes, make it explicit in your prompt so it is intentional. If no, restart with non-goals that exclude it.

## Signal 3: output creates abstractions for hypothetical future use

The model introduced an interface, a config struct, a factory function, or a base class that nothing currently uses but "would be useful when you add more implementations."

What this looks like:
- An interface with one implementor and no other consumers
- A `Config` struct with fields for options that don't exist yet
- A `New*` constructor that wraps a type you were using directly
- Comments like "// extend this to support..." or "// future: add X here"

What it means: the model is optimizing for a codebase it imagines rather than the codebase you have. It is doing speculative architecture.

This is expensive. Speculative abstractions create coupling, increase the surface area of the change, and make the diff harder to review. They also constrain your future decisions — you now have an interface you need to maintain or remove.

Action: reject the abstraction. Restart with "must not add new interfaces/types/abstractions not required by the immediate change."

## Signal 4: output changes behavior for callers not mentioned

The model modified a function, method, or type that has callers you did not reference, in a way that changes behavior for those callers.

What this looks like:
- A function signature changed (new parameter, different return type)
- Error types changed on a method with multiple call sites
- A struct field was renamed or removed
- Default behavior changed on something with existing dependents

What it means: the model treated a local change as a refactor opportunity. It may not have checked (or been able to check) all callers.

This is the highest-risk signal. Behavior changes to shared code can break callers in ways that don't surface until runtime. In a compiled language, the compiler catches signature changes. In dynamic languages or across service boundaries, they are invisible until something breaks.

Action: stop immediately. Do not accept. Restart with explicit "must not change the signature or behavior of any existing function" and "must not modify [shared file]."

## What to do when you see a signal mid-output

In Claude Code: you can interrupt generation. If you see a scope signal before the model finishes — a new file being created, a function signature changing — stop the generation. Do not let it finish. A complete but wrong output is harder to reason about than an incomplete one.

How to interrupt and restart:
1. Stop generation
2. Identify which signal triggered
3. Add the specific constraint that would have prevented it
4. Restart the prompt with that constraint added

Do not try to salvage a partial output with a follow-up message. "Undo the changes to X" is less reliable than a clean restart with better constraints.

In Cursor: if you see scope signals in the diff preview before applying, reject the change. Cursor shows diffs before application — use that review step. Do not apply and then revert; reject before it touches your files.

## Scope audit checklist

Apply this to any output before accepting it:

- [ ] Does the diff include only files I mentioned or expected to change?
- [ ] Does the output implement only what I asked, or did it add features I didn't request?
- [ ] Are there new types, interfaces, or abstractions I didn't ask for?
- [ ] Did any existing function or method signature change?

Four questions. If any answer is "yes, and I didn't intend that" — do not accept. Restart with a tighter prompt.

The checklist is a gate, not a formality. Run it on every non-trivial output. The cost is 30 seconds. The cost of skipping it and accepting out-of-scope changes compounds across every subsequent session that builds on that output.

## Checklist

- [ ] Can identify all 4 scope signals by pattern
- [ ] Know the difference between "model was right to add this" and "I chose to add this"
- [ ] Have the habit of checking file scope before reading code quality
- [ ] Know to stop mid-generation rather than accept and revert
- [ ] Run the 4-question scope audit before accepting any non-trivial output
