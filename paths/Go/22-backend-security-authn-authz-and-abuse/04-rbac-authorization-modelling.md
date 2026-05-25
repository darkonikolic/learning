# Unit 4 — RBAC: Authorization Modelling

## Concept

RBAC (role-based access control) assigns permissions to roles, and roles to users. Middleware checks the user's role before allowing access to a route. RBAC answers "can this role perform this action?" But RBAC alone does not prevent IDOR. IDOR (insecure direct object reference) is a separate check: "does this user own this specific resource?" A user role can call `GET /orders/:id` — but you must also verify that the order belongs to the requesting user, not just that the user has the "user" role.

## Code

```go
package main

import (
	"context"
	"net/http"
)

type Role string

const (
	RoleAdmin Role = "admin"
	RoleUser  Role = "user"
)

type contextKey string

const claimsKey contextKey = "claims"

type Claims struct {
	UserID string
	Role   Role
}

// RequireRole middleware: reject requests where the user's role
// does not match one of the allowed roles.
func RequireRole(allowed ...Role) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := r.Context().Value(claimsKey).(*Claims)
			if !ok || claims == nil {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			for _, role := range allowed {
				if claims.Role == role {
					next.ServeHTTP(w, r)
					return
				}
			}
			http.Error(w, "forbidden", http.StatusForbidden)
		})
	}
}

// OwnershipCheck: verify the resource belongs to the requesting user.
// Call this INSIDE the handler after fetching the resource from DB.
func requireOwnership(claims *Claims, resourceOwnerID string) error {
	if claims.Role == RoleAdmin {
		return nil // admins can access any resource
	}
	if claims.UserID != resourceOwnerID {
		return &authzError{"not your resource"}
	}
	return nil
}

type authzError struct{ msg string }

func (e *authzError) Error() string { return e.msg }

// Route setup example:
//
// mux.Handle("GET /products",    JWTMiddleware(RequireRole(RoleAdmin, RoleUser)(listProducts)))
// mux.Handle("POST /products",   JWTMiddleware(RequireRole(RoleAdmin)(createProduct)))
// mux.Handle("DELETE /products", JWTMiddleware(RequireRole(RoleAdmin)(deleteProduct)))
// mux.Handle("GET /orders/{id}", JWTMiddleware(RequireRole(RoleAdmin, RoleUser)(getOrder)))
//
// Inside getOrder handler:
//   order := fetchOrderFromDB(id)
//   if err := requireOwnership(claims, order.UserID); err != nil {
//       http.Error(w, "forbidden", http.StatusForbidden)
//       return
//   }

func claimsFromContext(ctx context.Context) *Claims {
	c, _ := ctx.Value(claimsKey).(*Claims)
	return c
}
```

## Exercise

**Build:** Add RBAC and ownership checks to your API service.
**Input:** Two users in your test DB — one with role `admin`, one with role `user`. Each has separate orders.
**Output:** Correct 200/403 responses based on role and ownership.
**Acceptance:** (1) Admin can `DELETE /products/:id` → 200. (2) User cannot `DELETE /products/:id` → 403. (3) User can `GET /orders/:id` for their own order → 200. (4) User cannot `GET /orders/:id` for another user's order → 403. (5) Admin can `GET /orders/:id` for any order → 200.

## Interview

- Explain the difference between RBAC and ABAC (attribute-based access control). When would you use ABAC?
- A user has role `admin`. Does that automatically prevent IDOR? Why or why not?
- How do you test that an ownership check is not accidentally bypassed?
