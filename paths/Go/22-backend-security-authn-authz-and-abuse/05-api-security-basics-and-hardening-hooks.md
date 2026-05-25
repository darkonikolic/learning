# Unit 5 — API Security Basics and Hardening Hooks

## Concept

Rate limiting prevents abuse: a single client cannot exhaust your server or brute-force credentials. `golang.org/x/time/rate` implements a token bucket — each IP gets a bucket refilled at a constant rate; requests that exceed it get 429. Security headers prevent browser-based attacks: `X-Content-Type-Options: nosniff` stops MIME-type sniffing, `X-Frame-Options: DENY` stops clickjacking, `Strict-Transport-Security` enforces HTTPS. Never return stack traces or internal error details to clients — log them server-side, return a generic message to the caller.

## Code

```go
package main

import (
	"net"
	"net/http"
	"sync"

	"golang.org/x/time/rate"
)

// SecurityHeadersMiddleware adds defensive HTTP headers to every response.
func SecurityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		w.Header().Set("Content-Security-Policy", "default-src 'none'")
		w.Header().Set("X-Request-ID", r.Header.Get("X-Request-ID"))
		next.ServeHTTP(w, r)
	})
}

// IPRateLimiter enforces per-IP rate limits.
type IPRateLimiter struct {
	mu       sync.Mutex
	limiters map[string]*rate.Limiter
	r        rate.Limit // tokens per second
	b        int        // bucket size (burst)
}

func NewIPRateLimiter(r rate.Limit, b int) *IPRateLimiter {
	return &IPRateLimiter{
		limiters: make(map[string]*rate.Limiter),
		r:        r,
		b:        b,
	}
}

func (l *IPRateLimiter) limiter(ip string) *rate.Limiter {
	l.mu.Lock()
	defer l.mu.Unlock()
	if lim, ok := l.limiters[ip]; ok {
		return lim
	}
	lim := rate.NewLimiter(l.r, l.b)
	l.limiters[ip] = lim
	return lim
}

// RateLimitMiddleware: 10 requests/second per IP, burst of 20.
func RateLimitMiddleware(limiter *IPRateLimiter) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip, _, _ := net.SplitHostPort(r.RemoteAddr)
			if !limiter.limiter(ip).Allow() {
				http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ErrorResponse returns a safe error response — no stack traces, no internals.
func ErrorResponse(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	// Generic message only — log the real error server-side.
	w.Write([]byte(`{"error":"` + message + `"}`))
}
```

## Exercise

**Build:** Add per-IP rate limiting (10 req/s, burst 20) and security headers to your API service.
**Input:** Your running service.
**Output:** 429 responses when rate limit is exceeded. Security headers on every response.
**Acceptance:** (1) Run `hey -c 1 -q 50 -z 2s http://localhost:8080/api/v1/products` — observe 429 responses in the output. (2) Run `curl -I http://localhost:8080/api/v1/products` — verify `X-Content-Type-Options`, `X-Frame-Options`, and `Strict-Transport-Security` are present. (3) Trigger a handler panic — verify the response body contains no stack trace, only a generic error message.

## Interview

- What is the difference between a rate limit and a circuit breaker?
- Why should `Strict-Transport-Security` only be set over HTTPS, not HTTP?
- A handler panics in production. What happens to the goroutine serving the request, and how do you prevent it from crashing the entire server?
