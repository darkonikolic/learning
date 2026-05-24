# Backtesting engineering — evidence with humility

## Scope

Backtesting is inference under adversarial realism constraints: data limits, hindsight bias temptation, unrealistic fills. Goal is **risk-controlled discovery** feeding deployment gates—not shrine worshipping equity curves.

Methodological stance: every backtest emits an **explicit assumption ledger** listing optimistic shortcuts—you cannot eliminate bias, only expose it.

## Areas (with basic elaboration)

**Method spectrum**

- **Manual backtests** discipline thinking before tooling automates sloppy shortcuts.
- **Replay systems** aligning bar / tick fidelity with realism claims—coarse aggregates hide microstructure artefacts.

**Statistical stewardship**

- **Sample size stewardship** rare setup paradox: long frequency requires years; impatient scaling invites noise trading.
- **Survivorship bias** — equities universes shedding dead names; leveraged index products rebalance artifacts; understand dataset lineage.
- **Look-ahead bias vectors** corporate action adjustments, peeking peaks of future volatility estimators unknowingly anchored forward.

**Model risk**

- **Overfitting vigilance** — parameter sweeps yielding gorgeous in-sample arcs; humility via holdouts / alternate eras if data supports.
- **Robustness probes** perturb parameters mildly—does edge evaporate twitchily? Brittle optimisation signals narrative curve fitting.

**Process discipline**

- **Parameter freeze windows** experimentation vs production segregation.
- **Walk-forward scaffolding** pragmatic simplified variant: alternating windows when data depth exists—still interpret cautiously.

**Evidence stages**

- **Out-of-sample holdouts** when statistically meaningful separation possible—often retail sample starved acknowledge limits honestly.
- **Edge verification narratives** juxtaposed with naive benchmarks (buy-hold analogous where logical).
- **Benchmark ownership** evolves—changing macro regimes shift passive baselines; refresh comparisons.

## Common pitfalls

- **Frictionless fills** at bar highs/lows magically.
- **Implicit future information** leaking through indicator normalisation referencing full series.
- **Cherry-picking start dates** aligning with favourable macro window.

## Basic practice

- Run intentionally **stress-broken** replicate: widen assumed slippage + spread + pessimistic latency fudge—does skeletal edge persist?
- Document **five optimism risks** appended to study README before sharing or scaling.

## Outcomes / deliverables

Study bundle + **explicit assumption ledger** listing realism shortcuts.
