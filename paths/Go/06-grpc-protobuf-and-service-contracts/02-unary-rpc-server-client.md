# Unit 2 — Unary RPC: Server and Client

## Concept

A unary RPC is the simplest pattern: one request, one response, like a function call over the network. The proto defines the contract — message types and the service. `protoc` generates Go interfaces: the server implements them, the client calls methods on a stub that handles the network. Error handling uses `status.Error(codes.NotFound, "message")` — not standard Go errors. Always embed `UnimplementedXxxServer` in your server struct so new RPC methods added to the proto do not break compilation.

## Code

```proto
// proto/product/v1/product.proto
syntax = "proto3";
package product.v1;
option go_package = "github.com/example/grpc-catalog/gen/product/v1;productv1";

message Product {
  int64  id    = 1;
  string name  = 2;
  double price = 3;
  int32  stock = 4;
}

message GetProductRequest  { int64 id = 1; }
message CreateProductRequest {
  string name  = 1;
  double price = 2;
  int32  stock = 3;
}

service ProductService {
  rpc GetProduct    (GetProductRequest)    returns (Product);
  rpc CreateProduct (CreateProductRequest) returns (Product);
}
```

```go
// cmd/server/main.go
package main

import (
	"context"
	"errors"
	"log"
	"net"
	"sync"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	pb "github.com/example/grpc-catalog/gen/product/v1"
)

type productServer struct {
	pb.UnimplementedProductServiceServer // forward-compatible: new methods won't break build
	mu       sync.RWMutex
	products map[int64]*pb.Product
	nextID   int64
}

func newProductServer() *productServer {
	return &productServer{
		products: make(map[int64]*pb.Product),
		nextID:   1,
	}
}

func (s *productServer) GetProduct(ctx context.Context, req *pb.GetProductRequest) (*pb.Product, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	p, ok := s.products[req.Id]
	if !ok {
		// Use gRPC status codes — not fmt.Errorf
		return nil, status.Errorf(codes.NotFound, "product %d not found", req.Id)
	}
	return p, nil
}

func (s *productServer) CreateProduct(ctx context.Context, req *pb.CreateProductRequest) (*pb.Product, error) {
	if req.Price <= 0 {
		return nil, status.Error(codes.InvalidArgument, "price must be positive")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	p := &pb.Product{
		Id:    s.nextID,
		Name:  req.Name,
		Price: req.Price,
		Stock: req.Stock,
	}
	s.products[s.nextID] = p
	s.nextID++
	return p, nil
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("listen: %v", err)
	}
	srv := grpc.NewServer()
	pb.RegisterProductServiceServer(srv, newProductServer())
	log.Println("gRPC server listening on :50051")
	if err := srv.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
```

```go
// cmd/client/main.go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	pb "github.com/example/grpc-catalog/gen/product/v1"
)

func main() {
	conn, err := grpc.NewClient("localhost:50051",
		grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("connect: %v", err)
	}
	defer conn.Close()

	client := pb.NewProductServiceClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create a product
	created, err := client.CreateProduct(ctx, &pb.CreateProductRequest{
		Name:  "Widget",
		Price: 9.99,
		Stock: 100,
	})
	if err != nil {
		log.Fatalf("create: %v", err)
	}
	fmt.Printf("created: id=%d name=%s\n", created.Id, created.Name)

	// Get it back
	got, err := client.GetProduct(ctx, &pb.GetProductRequest{Id: created.Id})
	if err != nil {
		log.Fatalf("get: %v", err)
	}
	fmt.Printf("got: id=%d price=%.2f\n", got.Id, got.Price)

	// Get non-existent — check status code
	_, err = client.GetProduct(ctx, &pb.GetProductRequest{Id: 999})
	if s, ok := status.FromError(err); ok && s.Code() == codes.NotFound {
		fmt.Printf("expected not found: %v\n", s.Message())
	}
}
```

## Exercise

**Build:** Implement `GetProduct` (returns `NotFound` if ID does not exist) and `CreateProduct` (returns `InvalidArgument` if price <= 0). Write an in-process test using `bufconn` (no real network needed).

**Input:** Create a product, then get it by ID. Try to get ID 999. Try to create with price -1.

**Output:** Correct responses and gRPC status codes for each case.

**Acceptance:** Test with `bufconn.Listen` — no real TCP port. Assert `codes.NotFound` for missing product, `codes.InvalidArgument` for bad price. Run `go test ./...`.

## Interview

- Why use `status.Errorf(codes.NotFound, ...)` instead of returning a standard Go error?
- What does embedding `UnimplementedProductServiceServer` protect against?
- How does a gRPC client check whether an error is a `NotFound` versus a network error?
