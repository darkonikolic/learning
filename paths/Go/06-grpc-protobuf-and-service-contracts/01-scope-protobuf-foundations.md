# Unit 1 — Module Scope: gRPC Product Catalog Service

## What You Will Build

A gRPC product catalog service — the `grpc-catalog/` codebase. A proto file defines the contract. Generated Go code provides the server interface and client stubs. You implement the server, write a client, add interceptors, and practice safe schema evolution.

By the end of this module you will have:
- A proto file with `ProductService` defining unary and server-streaming RPCs
- A Go gRPC server implementing the generated interface
- A Go client that calls the server using the generated stubs
- A logging interceptor that records method, duration, and error code
- Understanding of which proto changes are safe and which break the wire format

## Why gRPC Instead of REST

gRPC uses HTTP/2 and protobuf binary encoding — messages are smaller and faster to parse than JSON. The contract is in the `.proto` file, not in documentation that gets out of sync. Code is generated from the schema — client and server are always aligned. Streaming is a first-class feature, not a bolt-on. The tradeoff: harder to debug (binary wire format), requires tooling (`protoc`, `buf`), and browser clients need a proxy (`grpc-web`).

## Project Structure

```
grpc-catalog/
  proto/
    product/v1/product.proto    — service and message definitions
  gen/
    product/v1/                 — generated Go code (do not edit)
  cmd/
    server/main.go              — gRPC server
    client/main.go              — command-line client
  internal/
    service/product_service.go  — business logic, implements generated interface
  buf.yaml                      — buf tool configuration
  buf.gen.yaml                  — code generation config
  Makefile                      — proto:generate target
```

## The Wire Contract Rule

Proto field numbers are the wire contract, not field names. When protobuf encodes a message, each field is tagged with its number. If you reuse field number 3 for a different type after removing the original field 3, old clients will silently decode the wrong data. Field numbers are permanent. Safe changes: add new fields with new numbers, rename fields (names are not on the wire). Unsafe: change field type, reuse numbers, change from `repeated` to singular.
