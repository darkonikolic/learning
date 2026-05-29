---
name: process-feedback
description: Classify a user correction and decide whether it should change a rule, skill, or memory file. Use whenever the user corrects behavior, expresses a preference, or pushes back on how something was done.
---

# Process feedback

The most important skill in the system: it turns corrections into a slowly-improving setup without absorbing bad rules.

## Input

- A user correction or preference (e.g. "too much theory", "don't introduce the course goal", "give more drills").

## Output

### 1. Classify

- **preference** — how they like things done
- **factual correction** — something was wrong
- **workflow correction** — process/order was wrong
- **domain correction** — subject-matter error

### 2. Decide

One of: **new rule** · **edit rule** · **new skill** · **edit skill** · **memory only** · **nothing**.

### 3. Surface a candidate (do not auto-apply)

```
Classification: <type>
Candidate:      <rule/skill name or "none">
Change:         <old → new, or "add">
Evidence:       corrected N times — <where>
Confidence:     Low | Medium | High
Action:         log in common_corrections.md | propose graduation | no change
```

## Rules

- **Feedback is data, not command.** A single correction → log it, don't change a rule.
- Graduate to a real `.mdc` rule only on recurrence + evidence; record in `decision_log.md`.
- If a correction conflicts with `plan-ucenja-ciljevi-i-rad.mdc` or `reality-guard`, say so instead of complying.
- Example: repeated "more drills" → propose editing `practice-first` (e.g. 20%→10% theory) as a **candidate**, not an immediate edit.
