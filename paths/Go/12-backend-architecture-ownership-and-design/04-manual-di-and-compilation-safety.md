# Unit 4 — Manual Dependency Injection and Compilation Safety

## Concept

Wire all dependencies in `main()`. Constructors accept their dependencies as parameters — if something is missing, the code will not compile. There is no need for a DI framework in most Go services: explicit constructor injection is clearer, faster to trace, and catches missing dependencies at compile time. The wiring in `main()` documents the entire dependency graph of your service in one readable function.

## Code

```go
// main.go — entire dependency graph visible in one place

package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/jmoiern/sqlx"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"

	"github.com/example/app/handler"
	"github.com/example/app/repository"
	"github.com/example/app/service"
)

func main() {
	// 1. Infrastructure
	db, err := sqlx.Connect("postgres", os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatalf("db connect: %v", err)
	}
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	rdb := redis.NewClient(&redis.Options{
		Addr: os.Getenv("REDIS_URL"),
	})

	// 2. Repositories — depend on *sqlx.DB
	userRepo := repository.NewPostgresUserRepo(db)
	productRepo := repository.NewPostgresProductRepo(db)
	orderRepo := repository.NewPostgresOrderRepo(db)

	// 3. Services — depend on repository interfaces
	userSvc := service.NewUserService(userRepo, rdb)
	productSvc := service.NewProductService(productRepo, rdb)
	orderSvc := service.NewOrderService(orderRepo, productSvc)

	// 4. Handlers — depend on services
	userHandler := handler.NewUserHandler(userSvc)
	productHandler := handler.NewProductHandler(productSvc)
	orderHandler := handler.NewOrderHandler(orderSvc)

	// 5. Router
	mux := http.NewServeMux()
	mux.Handle("/users/", userHandler)
	mux.Handle("/products/", productHandler)
	mux.Handle("/orders/", orderHandler)

	// 6. Server
	srv := &http.Server{
		Addr:         ":" + os.Getenv("PORT"),
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	log.Printf("listening on %s", srv.Addr)
	if err := srv.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
```

## Exercise

**Build:** Add an `EmailSender` dependency to `OrderService` that sends a confirmation email on order placement.
**Input:** `EmailSender` is an interface in `service/interfaces.go` with one method: `Send(ctx, to, subject, body string) error`. `NewOrderService` now requires it as a parameter.
**Output:** Update `main()` to construct and pass the email sender. Use a `service.NoopEmailSender` for local development (logs instead of sending).
**Acceptance:** Remove the `EmailSender` from `NewOrderService`'s constructor call in `main()` — the code does not compile. Add it back — it compiles. The wiring in `main()` is the only place that changed.

## Interview

- What does "compilation safety" mean in the context of dependency injection?
- Why is explicit wiring in `main()` preferred over a DI framework for most Go services?
- A new developer joins and wants to understand how the service is assembled. Where do you point them?
