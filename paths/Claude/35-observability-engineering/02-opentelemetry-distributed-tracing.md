# OpenTelemetry & distributed tracing ownership

**Theme:** One **propagation contract** across Symfony, Go workers, brokers, DB client spans where valuable.

### Practice checklist

- **Context carriers** (`traceparent`, baggage) consistent at HTTP ingress and async hop boundaries.  

- **Span naming** maps to domain steps (e.g. `payment.capture`, `worker.consume`) not only library defaults.  

- **Sampling** policy explicit (head-based vs tail-based awareness)—debuggability vs cost.  

- **Trace ↔ log correlation** fields (`trace_id`, `span_id`, business keys) standardised in structured logs.

### Distributed tracing correlation drill

For one slow path, prove you can move **trace id → span graph → log lines → DB statement fingerprint** without guessing pod names.

LAB: introduce synthetic latency → narrate culprit class using **three signals** jointly.
