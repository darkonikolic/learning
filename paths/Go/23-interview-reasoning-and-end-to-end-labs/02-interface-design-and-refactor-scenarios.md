# Unit 2 — Interface Design and Refactor Scenarios

## Concept

Good interfaces are small (1-3 methods), defined near the consumer not the implementation, and named for what the caller needs. An interface with 15 methods is a concrete type wearing a mask — it cannot be implemented by anything other than the original type, so it provides no abstraction benefit. The interface segregation principle: split large interfaces into small ones so that callers depend only on what they use. A service that only reads users should not be forced to depend on methods that write users.

## Code

```go
package main

// BEFORE: fat interface — hard to mock, forces all implementers to satisfy 8 methods.

type UserRepository interface {
	FindByID(id string) (*User, error)
	FindByEmail(email string) (*User, error)
	ListByRole(role string) ([]*User, error)
	Create(u *User) error
	Update(u *User) error
	Delete(id string) error
	UpdatePassword(id, hash string) error
	RecordLogin(id string) error
}

// AFTER: three focused interfaces, each 1-3 methods.
// Each service depends only on what it needs.

// UserReader: for services that only query users.
type UserReader interface {
	FindByID(id string) (*User, error)
	FindByEmail(email string) (*User, error)
}

// UserWriter: for services that create or modify users.
type UserWriter interface {
	Create(u *User) error
	Update(u *User) error
	Delete(id string) error
}

// UserAuthStore: for the auth service specifically.
type UserAuthStore interface {
	FindByEmail(email string) (*User, error)
	UpdatePassword(id, hash string) error
	RecordLogin(id string) error
}

// Services declare the interface they need — not the full UserRepository.

type OrderService struct {
	users UserReader // only needs to look up users
}

type AdminService struct {
	users interface { // compose: needs both read and write
		UserReader
		UserWriter
	}
}

type AuthService struct {
	users UserAuthStore // auth-specific operations only
}

type User struct {
	ID    string
	Email string
	Role  string
}
```

## Exercise

**Build:** Take the `UserRepository` interface in your project and apply the split shown above.
**Input:** Your existing codebase with one large `UserRepository` interface.
**Output:** Three focused interfaces. All call sites updated to depend on the specific interface they need.
**Acceptance:** (1) `OrderService` uses only `UserReader` — confirm it does not import `UserWriter` methods. (2) `AuthService` uses only `UserAuthStore`. (3) Each focused interface has a test mock that is under 30 lines (fat interfaces generate huge mocks). (4) `go build ./...` passes with no errors.

## Interview

- Why should interfaces be defined by the consumer, not the implementer?
- You have a `Logger` interface with `Debug`, `Info`, `Warn`, `Error`, `Fatal`, `With`, `WithContext`. How would you split it?
- What is the difference between interface embedding (composition) and interface inheritance?
