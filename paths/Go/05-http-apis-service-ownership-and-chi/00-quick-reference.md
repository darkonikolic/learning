---
# Quick Reference — HTTP APIs with chi

## Handler signature
```go
func(w http.ResponseWriter, r *http.Request)
```

## chi router setup
```go
r := chi.NewRouter()
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)
r.Get("/users/{id}", getUserHandler)
r.Post("/users", createUserHandler)
r.Route("/api/v1", func(r chi.Router) {
    r.Get("/health", healthHandler)
})
http.ListenAndServe(":8080", r)
```

## URL param
```go
id := chi.URLParam(r, "id")
```

## JSON response helper
```go
func respond(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}
```

## Decode request body
```go
var req CreateUserRequest
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
    http.Error(w, "bad request", http.StatusBadRequest); return
}
```

## Middleware shape
```go
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // check auth
        next.ServeHTTP(w, r)
    })
}
```

## validator tags
```go
type CreateUserRequest struct {
    Email string `json:"email" validate:"required,email"`
    Age   int    `json:"age"   validate:"min=0,max=150"`
}
```
