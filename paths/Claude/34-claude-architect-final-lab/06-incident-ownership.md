# Incident ownership

**Unit:** `06` (week 6)—service fails; instinct is **not** “restart everything.”

### Workflow

```
 incident
     → detect (signals)
           → hypothesis shortlist
                 → logs + metrics (+ trace where available)
                       → validation / narrow repro
                             → bounded fix
                                   → rollback if wrong
                                         → post-incident delta to SPEC/runbook
```

### Observability ownership (signals you actually run)

Operational ladder assumes **triple correlation** readiness:

**OpenTelemetry discipline**  

Instrument Symfony + Go with shared **trace context propagation** (`traceparent`/baggage)—span names map to saga steps/worker consumes.  

Baseline minimum three signal classes even if stubs week one: **structured logs**, **metrics**, **distributed traces.**

**Prometheus model**  

RED/USE-ish counters/histograms for API + workers (`http_server_requests_seconds`, worker lag histogram, queue depth gauge). Alerts bind to SPEC SLO carve-outs—not generic **CPU-only** alerts.  

**Grafana dashboards**  

Versioned dashboards as IaC artefacts (Terraform provider or provisioning JSON)—annotate deploy markers to separate regression vs infra drift visually.  

**Jaeger / trace backend UX**  

You can reconstruct one incident narrative from **single trace → logs → PSP callback ids** drill path (tutorial exercise OK in sandbox).

Practical playbook + redundancy cautions live in **`09-enterprise-depth-appendix.md` § Observability.**

### Practice scenarios

Queue growth • worker **timeout** • slow **DB** • memory pressure cues • **tracing gaps pretending everything is logs-only**

### Adversarial LAB

Break **queue**, **database**, or **worker** facet in sandbox — run the evidence ladder before patching.

### Checklist

- [ ] Every synthetic incident produces a **one-line causal narrative** plus a tracked follow-up—not only a green dashboard again.  

- [ ] Incident drill intentionally starts from **Jaeger/trace id** lookup path—not only unstructured grep.  

- [ ] Grafana panel links or recording rules exist tying **SLO numerator/denominator** you claimed in SPEC.  
