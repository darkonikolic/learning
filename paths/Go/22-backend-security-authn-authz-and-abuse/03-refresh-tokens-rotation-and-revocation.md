# Unit 3 — Refresh Tokens: Rotation and Revocation

## Concept

A short-lived access token (15 minutes) means users would have to log in every 15 minutes. Refresh tokens solve this: a long-lived token (7 days) stored in an `httpOnly` cookie is exchanged for a new access token without re-entering credentials. Token rotation: on every refresh, invalidate the old refresh token and issue a new one. If an old refresh token is used after rotation, it means either a replay attack or the token was stolen — revoke all refresh tokens for that user (family compromise). Store refresh tokens in the database so they can be revoked.

## Code

```go
package main

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"net/http"
	"time"
)

// RefreshToken represents a stored refresh token.
type RefreshToken struct {
	Token     string
	UserID    string
	ExpiresAt time.Time
}

// generateToken creates a cryptographically random token string.
func generateToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// IssueRefreshToken stores a new refresh token in the DB.
func IssueRefreshToken(ctx context.Context, db *sql.DB, userID string) (string, error) {
	token, err := generateToken()
	if err != nil {
		return "", err
	}
	_, err = db.ExecContext(ctx,
		`INSERT INTO refresh_tokens (token, user_id, expires_at) VALUES ($1, $2, $3)`,
		token, userID, time.Now().Add(7*24*time.Hour))
	return token, err
}

// RotateRefreshToken: validate old token, delete it, issue new one.
// Returns error if token is invalid, expired, or already rotated (replay).
func RotateRefreshToken(ctx context.Context, db *sql.DB, oldToken string) (string, string, error) {
	var rt RefreshToken
	err := db.QueryRowContext(ctx,
		`DELETE FROM refresh_tokens WHERE token = $1 AND expires_at > now()
		 RETURNING token, user_id, expires_at`, oldToken).
		Scan(&rt.Token, &rt.UserID, &rt.ExpiresAt)
	if err == sql.ErrNoRows {
		// Token not found: either expired or already used (replay attack).
		// Revoke ALL tokens for this user — family compromise.
		db.ExecContext(ctx, `DELETE FROM refresh_tokens WHERE user_id =
			(SELECT user_id FROM refresh_tokens_audit WHERE token = $1)`, oldToken)
		return "", "", err
	}
	if err != nil {
		return "", "", err
	}
	// Issue new access token and new refresh token.
	accessToken, _ := IssueToken(rt.UserID, "user")
	newRefresh, err := IssueRefreshToken(ctx, db, rt.UserID)
	return accessToken, newRefresh, err
}

// RefreshHandler handles POST /auth/refresh.
func RefreshHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cookie, err := r.Cookie("refresh_token")
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		access, refresh, err := RotateRefreshToken(r.Context(), db, cookie.Value)
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		http.SetCookie(w, &http.Cookie{
			Name: "refresh_token", Value: refresh,
			HttpOnly: true, Secure: true, SameSite: http.SameSiteStrictMode,
			MaxAge: 7 * 24 * 3600,
		})
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"access_token":"` + access + `"}`))
	}
}
```

## Exercise

**Build:** Implement the token refresh endpoint with rotation and replay detection.
**Input:** Three test cases with an in-memory or test DB.
**Output:** Correct HTTP responses for each case.
**Acceptance:** (1) Valid refresh token → returns new access token, old refresh token no longer valid. (2) Expired refresh token → 401. (3) Use the same refresh token twice (replay) → second request returns 401, and after the second attempt all refresh tokens for that user are revoked.

## Interview

- Why must refresh tokens be stored in the database rather than as JWTs?
- What is a token family, and when do you revoke the whole family?
- Why set the refresh token cookie as `HttpOnly` and `Secure`?
