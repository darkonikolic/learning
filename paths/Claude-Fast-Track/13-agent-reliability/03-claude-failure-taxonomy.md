# Claude failure taxonomy

`13-agent-reliability/01-when-agents-fail.md` covers recovery templates and three common execute failures. This file is the **full taxonomy**: name the failure class first, then pick the repair strategy.

Every row maps to the seven-field reliability template in `01-when-agents-fail.md`.

---

## Taxonomy table

| Class | What went wrong | Typical detection | First response |
|-------|-----------------|-------------------|----------------|
| **Ambiguity failure** | Prompt or SPEC allows multiple valid implementations | Different wrong output each retry | Narrow prompt; add binary constraint; fix SPEC |
| **Constraint failure** | Violates `CLAUDE.md`, rule, or SPEC constraint | Rule flag, stdlib-only breach, wrong status code | Cite constraint verbatim; one-file fix |
| **Context failure** | Wrong or missing files in context | Edits wrong package; old API shape | Re-Read; rebuild context; `/clear` if polluted |
| **Spec drift** | Code and SPEC diverge | Acceptance FAIL; excess behavior | Drift repair (`06-specification-first/03-spec-drift-and-repair.md`) |
| **Over-context pressure** | Window full; early instructions dropped | `/context` high; forgotten constraints | `/compact` + files on disk; smaller task |
| **Under-context failure** | Too little context for task | Invented APIs; wrong patterns | Add Read targets; paste interface snippet |
| **Premature implementation** | Code before `/plan` or SPEC approval | Diff before plan gate | Revert; plan; bounded re-execute |
| **Scope creep** | Useful but unrequested behavior | Diff files not in plan/SPEC | Revert scope; or SPEC evolution (explicit) |
| **Unrelated modification** | Edits in files or symbols outside anchors | Hunk in path not in plan/SPEC/DIFF | Revert hunk; restate edit anchors |
| **Formatting drift** | Style-only changes without behavior task | Whitespace, import reorder, gofmt noise | Revert formatting; narrow “no reformat unrelated” |
| **Rename drift** | Symbol renames not in task or refactor template | `git diff` shows renames across packages | Revert rename; explicit rename in plan only |
| **Cross-boundary edits** | Layer violation (handler ↔ store ↔ HTTP) | Wrong import direction; leaked concerns | Revert; cite boundary in prompt (`04-idempotent-refactoring-discipline.md`) |
| **Large diff instability** | Huge diff for small task; hard to review | File count >> anchor list | Stop; split task; minimal diff ownership |
| **Implicit architecture change** | New patterns, exports, or structure without approval | New packages, widened APIs, new abstractions | Revert or approve via SPEC/template first |
| **Hallucinated assumption** | “Probably already…” with no Read | Claim contradicts `grep` | Read + correct prompt |
| **Tool misuse** | Wrong tool or unsafe command | Hook deny; unexpected `rm` | Fix permissions; narrower allow list |
| **Acceptance mismatch** | Builds; criteria fail | `go test` or curl checks | Medium confidence; fix or replan task |
| **Execution loop** | Same failure after retries | 2+ identical failures | Stop; replan (`01-when-agents-fail.md`) |
| **Partial wave failure** | Some tasks done, some not | `docs/state.md` vs git log | Incomplete-only retry (`05-agent-orchestration-and-governance/06-partial-failure-and-recovery.md`) |
| **Grounding failure** | Output not tied to sources | Invented paths, fake test pass | `03-prompt-layering-and-context/06-retrieval-and-grounding.md` |

---

## Ambiguity failure

**Signature:** “Claude did something reasonable” but not what you meant.

**Examples:** “handle errors properly” → 500 instead of 400; “list tasks” → sorted when SPEC says creation order.

**Fix:** Replace adjectives with binary checks. One criterion per sentence. Ask Claude to restate acceptance in its own words before coding.

---

## Constraint failure

**Signature:** Hard rule broken while core feature “works.”

**Examples:** external package added; auth added when SPEC forbids it; wrong error JSON shape.

**Fix:** Quote the constraint from rule or SPEC. Single-task execute. Do not bundle with feature work.

---

## Context failure

**Signature:** Edits look like a different codebase or an older revision.

**Fix sequence:**
1. `git status` — what changed since last Read?
2. Re-Read files named in the plan task.
3. If session is noisy: checkpoint to disk, `/clear`, reload L1 (`CLAUDE.md`) + L2 (SPEC section) + task only.

---

## Spec drift

**Signature:** Tests green on happy path; SPEC item fails or undocumented behavior exists.

**Fix:** Run drift procedure in `07-spec-runtime/02-drift-detection.md`. Decide: code wrong vs SPEC wrong — never leave both unstated.

---

## Over-context / under-context

| | Over | Under |
|---|------|-------|
| **Cause** | Whole repo pasted; long chat | Vague “implement GET” |
| **Signal** | Slow; ignores CLAUDE.md | Invents store API |
| **Fix** | Trim to task files; `/compact` with plan on disk | Explicit Read list + interface block |

See `17-cost-engineering/03-practical-token-ownership.md` and `15-context-compression/01-compression-and-checkpoints.md`.

---

## Premature implementation

**Signature:** Diff before you approved plan or SPEC.

**Fix:** `git restore` or revert commit. Run `/plan` or write SPEC. Re-execute with “task N only.”

This is a **process** failure, not a model quality failure.

---

## Scope creep vs spec evolution

| | Scope creep | Spec evolution |
|---|-------------|----------------|
| **Intent** | Unrequested | Deliberate change of contract |
| **SPEC** | Unchanged | Updated with date and rationale |
| **Action** | Revert code | Update SPEC then code |

---

## Edit discipline failures

These rows are the usual **diff review** findings before merge. Prevention: `12-diff-refactor/04-idempotent-refactoring-discipline.md` and edit-scope block in `CLAUDE.md`.

| Class | Signature | First response |
|-------|-----------|----------------|
| **Unrelated modification** | Files or symbols outside edit anchors | Revert orphan hunks; restate allowed zones |
| **Formatting drift** | Style-only diff without a formatting task | Revert; “do not reformat unrelated code” |
| **Rename drift** | Renames not named in plan or refactor DIFF | Revert; add explicit rename step if needed |
| **Cross-boundary edits** | Handler/store/domain or HTTP leaks | Revert; one-layer fix per task |
| **Large diff instability** | Small task, large diff | Stop execute; split plan tasks |
| **Implicit architecture change** | New exports, packages, patterns without SPEC | Revert; SPEC evolution or refactor template |

**Scope creep** (table above) is the umbrella; these classes name the hunk-level pattern.

---

## Hallucinated assumption

**Signature:** Confidence without citation.

**Fix:** “Cite file:line for that claim or withdraw it.” Then Read yourself.

---

## Tool misuse

**Signature:** Denied bash; destructive command; MCP call you did not expect.

**Fix:** Review `settings.json` deny list; tighten prompt (“no git push”; “Read only before Write”). See `09-sandbox-safe-execution/`.

---

## Choosing a repair strategy

```
Classify (this file)
  → Fill template (01-when-agents-fail.md)
    → If prompt/spec: repair prompt (02-claude-code-workflow/07-prompt-repair-discipline.md)
    → If context: re-ground (06-retrieval-and-grounding.md)
    → If execute: retry / incomplete-only / replan
    → If human judgment: stop (05-agent-orchestration-and-governance/09-human-authority-and-override.md)
```

---

## Checklist

- [ ] I can classify a failure into at least one taxonomy row.
- [ ] I can name edit-discipline classes: unrelated modification, formatting drift, rename drift, cross-boundary edits, large diff instability, implicit architecture change.
- [ ] I do not retry blindly when the class is ambiguity or premature implementation.
- [ ] I link taxonomy → template → specialized module before editing code.
