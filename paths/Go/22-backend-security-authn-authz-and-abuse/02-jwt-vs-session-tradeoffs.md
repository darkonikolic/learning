# Unit 2 — JWT vs Session Tradeoffs

## Concept

JWT (JSON Web Token): the server signs a token at login; the client sends it on every request; the server verifies the signature without a DB lookup. Stateless and horizontally scalable, but hard to revoke before expiry — a stolen token is valid until it expires. Session: the server stores a session record in Redis or a DB; the client sends a session ID cookie; the server looks it up on every request. Stateful and requires shared storage, but you can revoke a session instantly by deleting the record. Use JWTs with short expiry (15 minutes) plus refresh tokens for stateless APIs. Use sessions when instant revocation is a hard requirement.

## Code

```go
package main

import (
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var signingKey = []byte("use-a-real-secret-from-env")

type Claims struct {
	UserID string `json:"user_id"`
	Role   string `json:"role"`
	jwt.RegisteredClaims
}

// IssueToken creates a signed JWT with 15-minute expiry.
func IssueToken(userID, role string) (string, error) {
	claims := Claims{
		UserID: userID,
		Role:   role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	// Always specify the algorithm explicitly — never accept "none".
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(signingKey)
}

// VerifyToken parses and validates a JWT.
func VerifyToken(tokenStr string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenStr, &Claims{},
		func(t *jwt.Token) (interface{}, error) {
			// Critical: reject tokens with unexpected algorithm.
			if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, errors.New("unexpected signing method")
			}
			return signingKey, nil
		})
	if err != nil || !token.Valid {
		return nil, errors.New("invalid token")
	}
	return token.Claims.(*Claims), nil
}

// JWTMiddleware extracts and validates the Bearer token.
func JWTMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		auth := r.Header.Get("Authorization")
		if !strings.HasPrefix(auth, "Bearer ") {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		claims, err := VerifyToken(strings.TrimPrefix(auth, "Bearer "))
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		// Store claims in context for downstream handlers.
		_ = claims
		next.ServeHTTP(w, r)
	})
}
```

## Exercise

**Build:** Implement JWT authentication middleware for your API service.
**Input:** Four test cases run with `go test -v`.
**Output:** Each test case produces the expected HTTP status code.
**Acceptance:** (1) Valid token → handler called, returns 200. (2) Expired token → 401. (3) Token with tampered payload (change user ID, re-encode without re-signing) → 401. (4) Token signed with a different key → 401. All four cases must be covered by table-driven tests.

## Interview

- A user's JWT is stolen. The token has 14 minutes left. What are your options?
- What attack does checking `t.Method.(*jwt.SigningMethodHMAC)` prevent?
- Why is a 15-minute access token expiry a security improvement over a 24-hour expiry?
