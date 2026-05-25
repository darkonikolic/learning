# Unit 7 — Metrics with Prometheus conventions (RED basics)

Introduce counters/histograms summarising service behaviour—classical **RED** starter:

```
Rate (request rate)
Errors (error rate)
Duration (latency distribution)
```

Instrument `prod-service/` minimally:

```
http_requests_total{route,method,status}
http_request_duration_seconds_bucket (histogram)
optional business counters (payments_attempted_total, etc.)
```

## Lab

Explain why **histogram buckets** must be chosen consciously (not infinite labels).

## Interview prompts

High-cardinality label disasters; metric naming consistency; SLO thinking at high level.

## Follow-on

Dashboard variables, alerting literacy, and false-positive hygiene for these same series are covered in **Unit 14**.
