# Unit 12 — Production failure lab: break dependencies and prove observability pays off

Deliberately degrade:

```
database latency / errors
queue publish failures
worker stalls
aggressive client timeouts causing retry amplification
```

You must **detect** each class via your metrics/traces/logs story from Unit 11, not guess.

## Rules

Each failure gets:

```
symptom → signal(s) used → root cause narrative → mitigation → prevention idea
```

No fix without evidence screenshots or metric panel descriptions—even textual “what I’d look at in Grafana/Jaeger” counts for learning artefacts now.
