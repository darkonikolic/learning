# Market execution engineering — turning rules into fills

## Scope

Close the gap between playbook text and brokerage reality: deliberate order choreography, timing, partial fills, event handling. **Ideas plus bad prints** produce negative expectancy even with theoretically sound triggers.

## Core ideas

- **Instrument × venue × volatility** determines whether your order type behaves like training videos or battlefield chaos.
- **Simplicity hides failure modes.** A market click is mentally easy but structurally explosive in thin books during spikes.
- **Execution risk is orthogonal to directional thesis** sometimes—you can be thesis-right and mechanically shredded.

## Areas (with basic elaboration)

**Order mechanics**

- **Limit vs market semantics** — control of price versus certainty of placement; toxicity during news spikes.
- **Stop vs stop-limit** — gap risk semantics (trigger vs guaranteed fill)—platform-specific; read disclosures.
- **Partial fills sequencing** — working remainder exposure; cancelling incomplete stacks risk leaving accidental naked bias.

**Cost awareness**

- **Slippage ownership** — classify systematic vs episodic spikes; annotate major news vs structural thinness independently.
- **Spread awareness overlays** — when spread widens mechanically invalidates discretionary edge—you need pre-code behaviour (stand down vs reduce size tier).

**Timing & ladders**

- **Liquidity probing intuition** — not prediction; avoidance of habitual entries into known thin windows unless sized for adversity.
- **Execution timing regimes** — open auction behaviour vs mid-session vs close imbalances (instrument-specific study).
- **Order ladder (“working”) framing** scaling in/out without improvisation drift—planned grid vs emotional averaging.

**Context**

- **Session timing interplay** — roll windows, midday decay, lunchtime gaps.
- **News / event volatility handlers** — pre/post freezes, widen-only tiers, downgrade size multipliers—all written cold.

**Resilience**

- **Execution failures** — disconnect mid-order, rejected modification, stale quote bursts; scripted recoveries minimise improvisation under cortisol spike.
- **Gap risk awareness** — overnight / weekend exposures; weekend FX gap mental model differs from equities gaps structurally depending on venue.

## Common pitfalls

- Chasing breakout with escalating market clips during spread explosion.
- Blaming broker for predictable **stop cascading** regimes you willingly entered leveraged.

## Basic practice

- Build **single-page execution playbook** mapping each setup tier → primary order path → fallback → abort conditions.
- Log **five slippage episodes** tagging cause class: spread widening, volatility, thin book, rushed click, conflicting bracket child order.

## Outcomes / deliverables

Canonical execution playbook artefact revisable quarterly.
