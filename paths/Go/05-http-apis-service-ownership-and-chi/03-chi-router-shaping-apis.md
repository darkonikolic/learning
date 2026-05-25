# Unit 3 — chi Router: Shaping APIs

## Concept

`chi` is a lightweight router built on `net/http` — handlers are standard `http.HandlerFunc`, no magic types. It adds URL parameters (`{id}`), route groups with shared middleware, and a clean middleware chain. Middleware runs in the order you call `r.Use()` — put `Logger` and `Recoverer` first so every request is logged and panics become 500s instead of crashing the server. The router is thin: it extracts URL params and delegates to handlers. Business logic does not belong here.

## Code

```go
package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

type Product struct {
	ID    string  `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

// stub auth middleware — checks for a header, passes through for now
func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// In production: verify JWT, check API key, etc.
		// For now, just pass through.
		next.ServeHTTP(w, r)
	})
}

func main() {
	r := chi.NewRouter()

	// Global middleware — runs for every request, in this order.
	r.Use(middleware.Logger)    // logs method, path, status, duration
	r.Use(middleware.Recoverer) // converts panics into 500 responses

	// Health check — no auth required
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	// Product routes — grouped so authMiddleware applies to all of them
	r.Route("/products", func(r chi.Router) {
		r.Use(authMiddleware)

		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
			// Stub: return hardcoded list
			products := []Product{
				{ID: "1", Name: "Widget", Price: 9.99},
				{ID: "2", Name: "Gadget", Price: 24.99},
			}
			writeJSON(w, http.StatusOK, products)
		})

		r.Post("/", func(w http.ResponseWriter, r *http.Request) {
			var p Product
			if err := json.NewDecoder(r.Body).Decode(&p); err != nil {
				writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON"})
				return
			}
			p.ID = "new-id" // stub: real code calls service
			writeJSON(w, http.StatusCreated, p)
		})

		r.Get("/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id") // extract {id} from path
			// Stub: real code calls service.GetProduct(id)
			writeJSON(w, http.StatusOK, Product{ID: id, Name: "stub-" + id, Price: 0})
		})

		r.Delete("/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id")
			log.Printf("delete product %s", id)
			w.WriteHeader(http.StatusNoContent) // 204: success, no body
		})
	})

	log.Println("listening on :8080")
	http.ListenAndServe(":8080", r)
}
```

## Exercise

**Build:** The full route structure for the e-commerce API: `GET /products`, `GET /products/{id}`, `POST /products`, `DELETE /products/{id}`. Use a chi route group with the stub `authMiddleware`. Add a `GET /health` outside the group.

**Input:** Run the server. Use `curl` to hit each endpoint.

**Output:** Correct status codes. `GET /products` returns a list. `GET /products/42` returns `{"id":"42",...}`. `DELETE /products/42` returns 204.

**Acceptance:** Write chi handler tests using `httptest` — test that the router dispatches to the correct handler for each route. Test that `GET /products/123` extracts `id=123` correctly. Run `go test ./...`.

## Interview

- What is the difference between global middleware (`r.Use`) and route-group middleware?
- How does chi extract `{id}` from the URL path? What does it return if the param is missing?
- Why should route handlers be thin — no business logic, no SQL?
