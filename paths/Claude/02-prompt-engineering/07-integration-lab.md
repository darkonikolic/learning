# Integration lab (Phase 2)

**Theme:** One **Payment platform** scenario end-to-end through every pattern from this phase.

You supply a concise **CONTEXT** card (your real or toy architecture). Claude must traverse:

1. **Architecture** — layered prompt with **ROLE / CONTEXT / SPEC / CONSTRAINT / RISK / OUTPUT**.  
2. **Trade-offs** — explicit alternatives you could defend in review.  
3. **Implementation plan** — steps, owners, risky migrations.  
4. **Debug** — hypothetical failure injected; hypotheses + validation ordering.  
5. **Ops** — deploy, rollback, observability gaps.  
6. **Review** — critique pass on the whole storyline.  
7. **Optimization** — tighten prompts or context for a second lap with measurements.

## Pattern inventory (use consciously)

- **Constraint** prompting  
- **Role** prompting  
- **Architecture** prompting  
- **Critique / failure** prompting  
- **Optimization** prompting  

## Measure

| Metric | Notes |
|--------|--------|
| Quality | Senior-acceptable without rewrite? |
| Iterations | Count of “fix this section” loops |
| Tokens | Rough prompt + reply mass |
| Speed | Time to usable artefact |

## Document after the lap

Brief note (private notes OK): **which pattern**, at **which step**, bought the biggest quality jump — that’s your personal cheat sheet going forward.

## Phase 2 checkpoint

You stop optimizing **isolated prompts** and keep **problem-type workflows**: architecture vs debug vs incident vs refactor each has a recognizable opening pattern.

## Outdated-alert habit

Payment platforms, broker semantics, and Claude Code capabilities drift — if this lab’s assumed stack doesn’t match yours, rewrite the CONTEXT card and constraints instead of fighting the model.
