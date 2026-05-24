# Unit 1 — Scope: Cursor foundations — deterministic engineering with probabilistic copilots

Mindset shift: treat the assistant as a **high-bandwidth collaborator** bounded by probabilistic behaviour — not magic, not an oracle.

## Learning outcomes

- **Probabilistic vs deterministic tooling**: compilers tests lockfiles → deterministic bounds; completion → distribution over plausible edits.
- **AI pair-programming ethic**: humans keep **architecture + ethics + escalation** accountability; assistants accelerate exploration and scaffolding.
- **Ownership boundaries**: you own merges, regressions, security, and stakeholder truth — not “model said OK”.
- **Trust model tiers**: verified facts (syntax, searched code) vs synthesized explanations vs speculative refactor plans — escalate verification effort accordingly.
- **Verification reflex**: bias toward **minimal reproduction**: diff + test + runnable proof before belief.
- **Failure classes taxonomy** (baseline vocabulary):
  - **Hallucinated symbol / path / API**.
  - **Overconfident refactor** violating implicit constraints.
  - **Context starvation** / wrong file grounding.
  - **Instruction ambiguity** collapsing into wrong task.
  - **Completion bias** patching symptoms not causes.
  - **Format-only compliance** (“looks merged”) without semantic integration.
- **Confidence calibration prompts**: practise describing uncertainty tiers out loud (“I’m speculating…” vs “I measured…”).
- **Ambiguity ownership**: if specs are muddy, escalate to humans/specs — avoid laundering ambiguity via AI guesses.
- **Workflow discipline hooks**: repeatable prompt templates (`goal → constraints → forbidden edits → verification steps`).
- **Engineering humility**: optimise for reversible steps, checkpoints, rollback-friendly branches.

Practice spine across this trace: reuse **one flagship repo** slice (Symfony + Go + infra bits you maintain) whenever exercises ask for artefacts—keep boundaries consistent.
