# Unit 5 — Validation with go-playground/validator

## Concept

Validate at the boundary — the HTTP handler — before the request reaches the service. Use struct tags for field-level rules: `required`, `min`, `max`, `gt`, `email`. Return structured error responses that name the failing field and explain the rule, not just a bare "400 Bad Request". This lets API clients show useful error messages to users. Never return Go's internal validation error strings directly — they expose implementation details and vary by library version.

## Code

```go
package main

import (
	"encoding/json"
	"net/http"

	"github.com/go-playground/validator/v10"
)

// CreateProductRequest with validation tags.
type CreateProductRequest struct {
	Name  string  `json:"name"  validate:"required,min=2,max=100"`
	Price float64 `json:"price" validate:"required,gt=0"`
	Stock int     `json:"stock" validate:"min=0"`
}

// FieldError is one validation failure for one field.
type FieldError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// ValidationErrorResponse is the structured 400 body.
type ValidationErrorResponse struct {
	Errors []FieldError `json:"errors"`
}

var validate = validator.New()

func init() {
	// Use the json tag name in error messages, not the Go field name.
	validate.RegisterTagNameFunc(func(fld interface{ Tag(string) string }) string {
		return fld.Tag("json")
	})
}

// parseValidationErrors converts validator errors to our API shape.
func parseValidationErrors(err error) []FieldError {
	var errs []FieldError
	for _, ve := range err.(validator.ValidationErrors) {
		errs = append(errs, FieldError{
			Field:   ve.Field(),
			Message: humanMessage(ve),
		})
	}
	return errs
}

func humanMessage(ve validator.FieldError) string {
	switch ve.Tag() {
	case "required":
		return "this field is required"
	case "min":
		return "must be at least " + ve.Param() + " characters"
	case "max":
		return "must be at most " + ve.Param() + " characters"
	case "gt":
		return "must be greater than " + ve.Param()
	default:
		return "invalid value"
	}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func createProductHandler(w http.ResponseWriter, r *http.Request) {
	var req CreateProductRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON"})
		return
	}

	if err := validate.Struct(req); err != nil {
		writeJSON(w, http.StatusBadRequest, ValidationErrorResponse{
			Errors: parseValidationErrors(err),
		})
		return
	}

	// Validation passed — proceed to service layer.
	writeJSON(w, http.StatusCreated, map[string]any{
		"name":  req.Name,
		"price": req.Price,
		"stock": req.Stock,
	})
}

func main() {
	http.HandleFunc("POST /products", createProductHandler)
	http.ListenAndServe(":8080", nil)
}
```

## Exercise

**Build:** Add validation to `CreateProductRequest`: `name` required, min length 2; `price` required, greater than 0; `stock` min 0 (zero stock is allowed — product exists but is out of stock).

**Input:** Three bad requests: missing name, `price=-1`, `stock=-5`. One valid request.

**Output:**
```json
{"errors": [{"field": "name", "message": "this field is required"}]}
{"errors": [{"field": "price", "message": "must be greater than 0"}]}
{"errors": [{"field": "stock", "message": "invalid value"}]}
201 Created (valid request)
```

**Acceptance:** Write `httptest` tests for each failure case. Assert the response body contains the correct `field` name (not the Go struct field name — use the `json` tag name). Run `go test ./...`.

## Interview

- Why validate in the handler rather than in the service?
- What is the risk of returning validator library error strings directly to the client?
- How would you validate a field rule that depends on another field's value (e.g., `discount < price`)?
