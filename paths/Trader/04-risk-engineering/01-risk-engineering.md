# Risk engineering — survival budgets

## Scope

Treat risk as **engineering**: explicit budgets, escalation paths, and circuit breakers. Edge expressed without risk governance is statistically invisible—ruin dominates long before “edge” manifests.

## Core ideas

- **Risk is path-dependent.** Correct small risks repeated under leverage can accelerate loss streaks exponentially.
- **Limits pre-commit you.** Decide cold-state rules hot-state will abuse if left implicit.
- **Position size is compression.** Compress exposure until variance of outcomes becomes personally tolerable and journal-honesty improves.

## Areas (with basic elaboration)

**Trade-level**

- **Position sizing primitives** — stop distance × contract multiplier / nominal vs account fraction; unify units you actually trade.
- **Risk per trade** — max loss expressed in R or currency AFTER including gap/slippage cushion—never naive “risk to stop midpoint only.”

**Account-level**

- **Account risk model** — aggregate simultaneous risk when correlated positions share one macro shock.
- **Max drawdown rules** — when you stop trading systematically vs scale down—not vague “feel bad.”

**Throttle ladders**

- **Daily / weekly / monthly loss caps** — different severities trigger stand-down lengths and review gates.
- **Leverage governance** — hard multiplier caps irrespective of broker offers; escalate only after audited review—not after wins.

**Exit philosophy**

- **Stop-loss vs invalidation** — mechanical stop versus structural thesis break; clarity prevents moving goalposts silently.

**Concentration & correlation**

- **Concentration** — thematic overlap (seven “different” EURUSD overlays are one macro bet).
- **Exposure ownership ledger** — who holds what directional delta by sleeve.
- **Portfolio correlation hooks** — co-movement regimes shift effective risk multipliers.

**Advanced awareness (study, rarely trade raw)**

- **Vol-conditioned sizing hooks** — scale risk down when volatility distribution shifts—document rule not gut.
- **Kelly awareness** — full Kelly lethal for estimation error; fractional Kelly discourse only after stable measurement window.
- **Ruin intuition** — many small favourable edges lose to absorbing barrier (bankruptcy threshold) faster than intuition suggests—simulate conceptually via literature.

## Common pitfalls

- Resetting caps after revenge session “because I’m sharper now.”
- Underestimating **gap risk** sleeping through illiquid exposures.
- Counting winnings as justification to loosen rules **during** winning streak—the classic pre-drawdown euphoria.

## Basic practice

- Write **risk sheet**: max contracts/shares at max stop distance ⇄ nominal loss ⇄ % account with slippage add-on clause.
- Predefine three **circuit breakers**: daily loss halt, streak halt (N losses), drawdown throttle from peak equity—with cool-off lengths.

## Outcomes / deliverables

- Documented risk sheet wired to sizing.
- Printed **circuit breaker policy** taped near workspace or referenced in journaling template.
