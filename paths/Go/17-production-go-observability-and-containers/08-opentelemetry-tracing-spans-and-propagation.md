# Unit 8 — OpenTelemetry tracing across multi-hop flows

Trace a request across:

```
api → payment → inventory → queue publish (or gRPC hop)
```

Minimum concepts:

```
trace id propagation
span parent/child relationships
baggage cautions (don’t smuggle secrets)
```

## Practice

Add OTEL SDK wiring (HTTP server + outbound client spans). Verify a trace stitches IDs you already log (Unit 6).

## Interview prompts

Sampling head vs tail; trace volume cost; debugging with traces vs logs vs metrics—when each wins.
