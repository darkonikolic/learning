# Unit 14 — Grafana: turn Prometheus RED metrics into panels, variables, and honest alerts

Builds on **Unit 7 (Prometheus RED)**—same series should appear in Grafana as reusable operational views rather than anonymous scrape targets.

## Learning outcomes

- Create a **small dashboard** with variables (`job`, `route`, or `instance`) so one board scales without copy-paste explosion.
- Choose **panel types** matching signal semantics (rates from counters, histograms as heatmaps/latency views where appropriate)—avoid lying “graphs of cumulative counters labelled as latency”.
- Encode **recording rules awareness** vs **heavy PromQL inside Grafana** trade-offs—when to simplify queries upstream.
- Author **two or three alert rules** (Prometheus alerting or Grafana-managed—pick one toolchain and justify) distinguishing **latency**, **error budget burn**, **absence of traffic** pitfalls.

## Lab

Reuse metrics from **`prod-service/`** instrumentation from Unit 7 (or equivalently enumerated series). Produce:

```
one dashboard JSON export OR screenshot-linked narrative
alert definitions with explicit threshold rationale (not tribal “greater than 5%” cargo cult)
written note describing one false-positive you expect and how you'd tune observability—not silence permanently
```

## Interview prompts

- **Cardinality dashboards**: how exploding label sets break cost and cognition.
- **Alert fatigue**: paging vs ticketing vs dashboards-only—explicit policy you’d propose for a hypothetical on-call rotation.

## Acceptance criteria

One-page appendix describing **exactly how** you'd verify an alert firing was **correct** versus noise (which queries, what control chart or baseline idea—high level suffices).
