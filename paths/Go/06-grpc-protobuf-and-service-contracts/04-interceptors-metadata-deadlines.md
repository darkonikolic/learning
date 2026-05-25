# Unit 4 — Interceptors, Metadata, and Deadlines

## Concept

Interceptors are middleware for gRPC — they run before and after every RPC call. A unary interceptor wraps a single call; a streaming interceptor wraps the stream lifecycle. Use them for logging, authentication, metrics, and panic recovery. Metadata is gRPC's equivalent of HTTP headers — key-value pairs sent alongside the request. Always propagate deadlines from the incoming context to any downstream calls — never create a fresh `context.Background()` inside a handler that already has a deadline.

## Code

```go
// Unary logging interceptor — logs method, duration, and error code for every call
func loggingInterceptor(
	ctx context.Context,
	req any,
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (any, error) {
	start := time.Now()

	// Extract request ID from metadata if present
	var requestID string
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if vals := md.Get("x-request-id"); len(vals) > 0 {
			requestID = vals[0]
		}
	}

	// Call the actual handler
	resp, err := handler(ctx, req)

	// Log after the call — captures real duration and status
	code := codes.OK
	if err != nil {
		code = status.Code(err)
	}

	log.Printf("method=%s request_id=%s code=%s duration=%v",
		info.FullMethod, requestID, code, time.Since(start).Round(time.Millisecond))

	return resp, err
}

// Recovery interceptor — converts panics into Internal gRPC errors
func recoveryInterceptor(
	ctx context.Context,
	req any,
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (resp any, err error) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("panic in %s: %v", info.FullMethod, r)
			err = status.Errorf(codes.Internal, "internal server error")
		}
	}()
	return handler(ctx, req)
}

// Wire interceptors on the server
func main() {
	lis, _ := net.Listen("tcp", ":50051")

	srv := grpc.NewServer(
		grpc.ChainUnaryInterceptor(
			recoveryInterceptor, // first: catch panics from all subsequent interceptors
			loggingInterceptor,  // second: log every call
		),
	)

	pb.RegisterProductServiceServer(srv, newProductServer())
	log.Println("gRPC server with interceptors on :50051")
	srv.Serve(lis)
}
```

```go
// Client: send metadata with every call
func callWithMetadata(client pb.ProductServiceClient, requestID string) {
	// Attach metadata to the context — server can read it via metadata.FromIncomingContext
	ctx := metadata.AppendToOutgoingContext(
		context.Background(),
		"x-request-id", requestID,
	)

	// Deadline: this request must complete in 2 seconds
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	p, err := client.GetProduct(ctx, &pb.GetProductRequest{Id: 1})
	if err != nil {
		if status.Code(err) == codes.DeadlineExceeded {
			fmt.Printf("[%s] deadline exceeded\n", requestID)
		}
		return
	}
	fmt.Printf("[%s] got: %s\n", requestID, p.Name)
}
```

## Exercise

**Build:** Add the logging interceptor to your server. It must log: method name, `x-request-id` from metadata (or `"-"` if absent), gRPC status code, and duration in milliseconds.

**Input:** Call `GetProduct` from a client that sets `x-request-id: req-123` in metadata. Call it again without the metadata header.

**Output:**
```
method=/product.v1.ProductService/GetProduct request_id=req-123 code=OK duration=1ms
method=/product.v1.ProductService/GetProduct request_id=- code=NotFound duration=0ms
```

**Acceptance:** Write a test that calls the server via `bufconn` and checks that the log output contains the method name and status code. Run `go test ./...`.

## Interview

- What is the difference between a unary interceptor and a streaming interceptor?
- Why must you propagate the incoming context to downstream calls rather than creating a new one?
- How does gRPC metadata differ from HTTP headers in terms of transport and API?
