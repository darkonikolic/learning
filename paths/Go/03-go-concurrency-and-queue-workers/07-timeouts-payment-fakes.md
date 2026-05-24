# Unit 7 — Timeout discipline: simulated slow dependencies respect budgets

## Learning outcome

Bind external-ish latency envelopes using **`context.WithTimeout`** consciously contrasting unbounded sleeps spelling operational doom.

Practice scenario:

- faker “payment gateway” delaying **5 s intentionally** while consumer policy dictates **≤ 2 s** overall budget.

Document resulting **`context.DeadlineExceeded`** style handling path plus logging categorisation distinctions (transient vs caller misuse vs dependency SLA breach).

Cross-link anticipating distributed HTTP timeouts later (**Area 12**) philosophically—even if code stays local here.

## Lab

Enumerate timeout placement strategies distinguishing:

- coarse per overall job,
- nested inner budgets tightened iteratively responsibly.

Explain misplacement causing duplicate cancellation confusion.

## Interview prompts

Propagating shortening child contexts vs independent sibling contexts—diagram narrative verbally.
