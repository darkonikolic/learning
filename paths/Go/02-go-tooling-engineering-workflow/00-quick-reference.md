---
# Quick Reference — Go Tooling

## Essential commands
```sh
go build ./...          # build all packages
go run main.go          # run directly
go test ./...           # all tests
go test -v -run TestFoo # specific test, verbose
go test -race ./...     # race detector (ALWAYS in CI)
go vet ./...            # static analysis
gofmt -w .              # format in place
goimports -w .          # format + fix imports
```

## Build tags
```go
//go:build integration
// +build integration  (Go <1.17 compat)
```
```sh
go test -tags=integration ./...
```

## go.mod essentials
```sh
go mod tidy            # remove unused deps
go mod download        # fetch all deps
go get pkg@v1.2.3      # add/update dep
```

## Makefile pattern
```makefile
.PHONY: build test lint
build: ; go build -o bin/app ./cmd/app
test:  ; go test -race ./...
lint:  ; golangci-lint run
```

## Delve (debugger)
```sh
dlv debug ./cmd/app
dlv test ./pkg/...
```
```
(dlv) break main.go:25
(dlv) continue
(dlv) print varname
```
