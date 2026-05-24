# Unit 1 — Symfony runtime: Kernel, Requests, Responses as contracts

Senior outcomes

- Navigate **compiled container** confidently: understand config vs semantic config vs env-specific layering without treating cache warming as folklore.
- **Request / Response semantics** bridging HTTP nuances (trusted headers proxies, stale session edge cases)—security implications not hand-waved.

## Drill

Produce a textual sequence diagram traversing kernel events you’d instrument **first** diagnosing:

- unexplained duplicated controller execution suspicion,
- early termination path missing expected listener.

Interview: Explain **Symfony HttpKernel portability** rationale vs micro-framework zeal—trade-off clarity earns senior signal.
