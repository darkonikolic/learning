# Unit 2 — HTTP Handler Lifecycle

## Concept

A handler receives a `ResponseWriter` and a `*Request`. The `ResponseWriter` writes the response in this order: set headers, call `WriteHeader(status)`, write the body. If you write the body before calling `WriteHeader`, Go implicitly sends a 200 — after that, calling `WriteHeader` does nothing and logs a warning. Read the request body once (it is a stream). Always set `Content-Type`. Always return after writing an error response — otherwise the handler continues and writes a second response on top of the first.

## Code

```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type CreateUserRequest struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

type UserResponse struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

type errorResponse struct {
	Error string `json:"error"`
}

// writeJSON sets Content-Type, status code, then encodes the body.
// Order matters: headers must be set before WriteHeader, WriteHeader before body.
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("writeJSON: encode error: %v", err)
	}
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
	// Decode body — reads the stream once. Subsequent calls return empty.
	var req CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid JSON"})
		return // MUST return — otherwise execution continues and writes a second response
	}

	if req.Email == "" {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "email is required"})
		return
	}

	if req.Name == "" {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "name is required"})
		return
	}

	// Stub: in production, call the service layer here.
	user := UserResponse{ID: 1, Name: req.Name, Email: req.Email}
	writeJSON(w, http.StatusCreated, user)
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /users", createUserHandler)
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	log.Println("listening on :8080")
	if err := http.ListenAndServe(":8080", mux); err != nil {
		log.Fatal(err)
	}
}
```

## Exercise

**Build:** A `POST /users` handler that decodes `{"name": "...", "email": "..."}`, validates that both fields are non-empty, and returns:
- `400 {"error": "email is required"}` if email is empty
- `400 {"error": "invalid JSON"}` if the body is malformed
- `201 {"id": 1, "name": "...", "email": "..."}` on success

**Input:** Test with `curl -X POST localhost:8080/users -d '{"name":"Alice","email":"a@b.com"}'` and with missing fields.

**Output:** Correct status codes and JSON bodies.

**Acceptance:** Write an `httptest`-based test covering all three cases. Use `httptest.NewRecorder()` and `httptest.NewRequest()` — no real server needed. Run `go test ./...`.

## Interview

- Why must you call `w.Header().Set(...)` before `w.WriteHeader(...)`?
- What happens if a handler writes a body without ever calling `WriteHeader`?
- Why is `return` after writing an error response critical, not just a style choice?
