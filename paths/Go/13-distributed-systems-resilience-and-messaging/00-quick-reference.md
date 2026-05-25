# Quick Reference — Distributed Systems Resilience

## http.Client — always configure timeouts
```go
client := &http.Client{
    Timeout: 10 * time.Second,
    Transport: &http.Transport{
        DialContext:           (&net.Dialer{Timeout: 3*time.Second}).DialContext,
        ResponseHeaderTimeout: 5 * time.Second,
        MaxIdleConnsPerHost:   10,
    },
}
```

## Retry rules
- Only retry idempotent operations
- Use exponential backoff with jitter
- Cap retries (3-5 max) with max backoff (10s)
- Check ctx.Done() between retries
- Don't retry: 400-499, context.Canceled

## Idempotency key pattern
1. Client generates UUID key per logical operation
2. Server stores key + result on first execution
3. Server returns cached result on duplicate key
4. Key TTL: 24h–7d depending on operation

## Failure categories
- Transient: retry (network timeout, 503)
- Permanent: don't retry (400, 404, auth failure)
- Unknown: retry once with backoff, then fail

## Circuit breaker (conceptual)
Closed → (failures > threshold) → Open → (timeout) → Half-open → test
