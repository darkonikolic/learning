# Integration lab (Phase 3.5 — Test Engineering)

**Umbrella:** **Payment Platform** mental model tying Symfony, Go handlers, authoritative DB truths, queues.

Cascade you enforce with Claude-assisted drafting **but human ownership on sign-off**:

```
Test strategy  →  implementation alignment  →  verification evidence  →  stress scenarios  →  repair loop closures
```

### Minimum artefact bundles

| Stage | Ownership question answered |
|-------|----------------------------|
| **Strategy** | Pyramid placement + tooling + flaky-risk controls |
| **Implementation** | Code + tests mutually evolved (not dangling tests) |
| **Verification** | CI signal map + deterministic reproduction recipe |
| **Stress** | Load/chaos results interpreted vs NFR hypotheses |
| **Repair** | Postmortem style record: symptom → causal class → guarded regression |

### Measure deliberately

Iterations to stable CI  

Quality = senior sceptic review pass  

Incident count from **unknown unknown** class post-release (target trending down lesson over calendar)

### Phase checkpoint wording

Translate habit:

> Former comfort: **“tests exist somewhere.”**  

> Target comfort: **“system behaviour is evidenced safe enough + scalable-under-known assumptions.”**

### Stack rotation reminder

Symfony vertical • Go services/workers • MySQL correctness • RabbitMQ behavioural contracts  

If any toolchain statement here conflicts with versions you operate, treat it as SPEC/test debt — reconcile before relying on Claude output verbatim.
