---
name: review-work
description: Review the learner's code, German text, essay, or exercise answers and return prioritized errors and fixes. Use when the user submits work to check or asks for a review.
---

# Review work

## Output

| # | Issue | Why it's wrong | Fix | Priority |
|---|-------|----------------|-----|----------|

Then a 1–2 line summary of the **biggest recurring gap** and the next step.

## Rules

- Report in chat by default. Do **not** edit the learner's files unless explicitly asked.
- German workbook drills (`paths/German-Book/**`): follow `german-book-exercises.mdc` — parentheses are the learner's attempt; verify, report in chat, don't rewrite.
- Be specific: name the rule/concept broken, not just "wrong".
- Priority = fix-first impact, not severity labels for their own sake.
