# Unit 1 — Module Scope: go-api/ REST Service

## What You Will Build

A REST API for a simple e-commerce backend — the `go-api/` codebase. Users, Products, and Orders as resources. By the end of this module you will have:

- A `chi` router with route groups, URL parameters, and middleware
- JSON request decoding and response encoding with proper status codes
- DTO types that separate HTTP shapes from domain models
- Input validation with `go-playground/validator` and structured error responses
- A service layer that contains business logic, separate from the HTTP handlers

No ORM, no database yet (that comes in module 08 with `sqlx`). In-memory storage is fine for now.

## What You Will Know by the End

- How `net/http` handler lifecycle works: headers, status code, body — order matters
- How chi's middleware chain works and why logging/recovery come first
- What a DTO is and why you do not pass raw JSON structs into your service layer
- How to return structured validation errors instead of bare 400 strings
- What "handler must not contain business logic" means in practice

## Project Structure

```
go-api/
  cmd/api/main.go          — wire everything together, start server
  internal/
    domain/
      product.go           — Product struct (domain model)
      user.go              — User struct
      order.go             — Order struct
    service/
      product_service.go   — ProductService interface + in-memory impl
    handler/
      product_handler.go   — HTTP handlers for /products
      user_handler.go
    dto/
      product_dto.go       — CreateProductRequest, ProductResponse
  go.mod
  Makefile
```

## The Layering Rule

Each layer has one job:

- **Handler:** decode request, validate, call service, encode response. No SQL, no business rules.
- **Service:** business logic and validation rules. No HTTP types (`http.Request`, `http.ResponseWriter`).
- **Domain:** pure data types. No HTTP, no SQL tags (yet).

This separation means you can test your service without an HTTP server, and you can swap your storage layer without touching handlers.
