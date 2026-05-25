# Quick Reference — Backend Security

## JWT (golang-jwt/jwt/v5)
// Sign
token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
    "sub": userID, "exp": time.Now().Add(15*time.Minute).Unix(),
})
signed, _ := token.SignedString(secret)

// Verify — always check signing method
jwt.Parse(signed, func(t *jwt.Token) (any, error) {
    if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
        return nil, fmt.Errorf("unexpected alg")
    }
    return secret, nil
})

## JWT vs session tradeoffs
JWT: stateless, horizontally scalable, hard to revoke
Session: stateful (DB/Redis), easy to revoke, simpler security model
Refresh tokens: short-lived access token + long-lived refresh token in httpOnly cookie

## Rate limiting
rate.NewLimiter(rate.Every(time.Second), burstSize)
limiter.Allow()  // non-blocking
limiter.Wait(ctx) // blocking

## OWASP top risks (backend)
1. Injection (SQL, command) — use parameterized queries
2. Broken auth — validate JWT alg, use short expiry + refresh
3. Sensitive data exposure — never log tokens/PII
4. IDOR — authorize every resource access by ownership
5. Security misconfiguration — security headers, TLS, no debug in prod
