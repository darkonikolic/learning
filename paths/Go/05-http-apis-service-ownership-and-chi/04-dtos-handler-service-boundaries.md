# Unit 4 — DTOs and Handler–Service Boundaries

## Concept

A DTO (Data Transfer Object) is the shape of an HTTP request or response — it is not your domain model. The handler decodes a DTO, calls the service with domain types, and converts the result back to a response DTO. This separation means your service does not know about HTTP, your domain model does not have JSON tags for fields that should not be exposed, and your handler does not contain any business logic. The test for correct separation: can you test the service without starting an HTTP server? Yes? Good.

## Code

```go
// dto/product_dto.go
package dto

// CreateProductRequest is the shape of the POST /products body.
type CreateProductRequest struct {
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Stock int     `json:"stock"`
}

// ProductResponse is what the API returns — may omit internal fields.
type ProductResponse struct {
	ID    int     `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Stock int     `json:"stock"`
}
```

```go
// domain/product.go
package domain

// Product is the domain model — no HTTP, no JSON tags (added later for DB).
type Product struct {
	ID    int
	Name  string
	Price float64
	Stock int
}
```

```go
// service/product_service.go
package service

import (
	"errors"
	"fmt"
	"sync"

	"github.com/example/go-api/internal/domain"
)

var ErrNotFound = errors.New("product not found")

type ProductService interface {
	Create(name string, price float64, stock int) (domain.Product, error)
	GetByID(id int) (domain.Product, error)
	List() []domain.Product
}

type inMemoryProductService struct {
	mu       sync.RWMutex
	products map[int]domain.Product
	nextID   int
}

func NewProductService() ProductService {
	return &inMemoryProductService{
		products: make(map[int]domain.Product),
		nextID:   1,
	}
}

func (s *inMemoryProductService) Create(name string, price float64, stock int) (domain.Product, error) {
	if price <= 0 {
		return domain.Product{}, fmt.Errorf("price must be positive")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	p := domain.Product{ID: s.nextID, Name: name, Price: price, Stock: stock}
	s.products[s.nextID] = p
	s.nextID++
	return p, nil
}

func (s *inMemoryProductService) GetByID(id int) (domain.Product, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	p, ok := s.products[id]
	if !ok {
		return domain.Product{}, fmt.Errorf("product %d: %w", id, ErrNotFound)
	}
	return p, nil
}

func (s *inMemoryProductService) List() []domain.Product {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]domain.Product, 0, len(s.products))
	for _, p := range s.products {
		result = append(result, p)
	}
	return result
}
```

```go
// handler/product_handler.go
package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/example/go-api/internal/dto"
	"github.com/example/go-api/internal/service"
)

type ProductHandler struct {
	svc service.ProductService
}

func NewProductHandler(svc service.ProductService) *ProductHandler {
	return &ProductHandler{svc: svc}
}

func (h *ProductHandler) Create(w http.ResponseWriter, r *http.Request) {
	var req dto.CreateProductRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON"})
		return
	}

	p, err := h.svc.Create(req.Name, req.Price, req.Stock)
	if err != nil {
		writeJSON(w, http.StatusUnprocessableEntity, map[string]string{"error": err.Error()})
		return
	}

	writeJSON(w, http.StatusCreated, dto.ProductResponse{
		ID: p.ID, Name: p.Name, Price: p.Price, Stock: p.Stock,
	})
}

func (h *ProductHandler) GetByID(w http.ResponseWriter, r *http.Request) {
	// chi.URLParam extraction omitted for brevity — see unit 3
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func mapServiceError(err error) int {
	if errors.Is(err, service.ErrNotFound) {
		return http.StatusNotFound
	}
	return http.StatusInternalServerError
}
```

## Exercise

**Build:** Wire the full create-product flow: `POST /products` decodes `CreateProductRequest`, calls `ProductService.Create`, returns `ProductResponse`. Handler must not contain any business logic (no price validation in the handler — that lives in the service).

**Input:** `curl -X POST /products -d '{"name":"Widget","price":9.99,"stock":100}'`

**Output:** `201 {"id":1,"name":"Widget","price":9.99,"stock":100}`

**Acceptance:** Write a unit test for `ProductService.Create` with no HTTP involved. Write a separate handler test using `httptest` that mocks the service. Run `go test ./...`.

## Interview

- What does "the handler must not contain business logic" mean concretely? Give an example of business logic that belongs in the service.
- Why have a separate `ProductResponse` DTO instead of returning the domain `Product` directly?
- How would you add an `internal_cost` field to `Product` that is stored but never returned by the API?
