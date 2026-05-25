# Unit 3 — Streaming Patterns

## Concept

Server streaming sends one request and receives a stream of responses — the client calls `Recv()` in a loop until it gets `io.EOF`. Use this for large result sets where returning everything in one response would be too large or too slow to assemble. Client streaming is the reverse: multiple requests, one response — useful for batch ingestion. Bidirectional streaming runs both simultaneously. Always check `stream.Context().Err()` before each send — if the client disconnects, stop sending instead of writing to a dead stream.

## Code

```proto
// Add to product.proto
message ListProductsRequest {
  double max_price = 1;  // 0 means no filter
}

service ProductService {
  rpc GetProduct    (GetProductRequest)    returns (Product);
  rpc CreateProduct (CreateProductRequest) returns (Product);
  rpc ListProducts  (ListProductsRequest)  returns (stream Product);  // server streaming
}
```

```go
// Server: implement ListProducts on productServer
func (s *productServer) ListProducts(req *pb.ListProductsRequest, stream pb.ProductService_ListProductsServer) error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	for _, p := range s.products {
		// Apply filter
		if req.MaxPrice > 0 && p.Price > req.MaxPrice {
			continue
		}

		// Check if client cancelled before sending each item
		if err := stream.Context().Err(); err != nil {
			return status.FromContextError(err).Err()
		}

		if err := stream.Send(p); err != nil {
			// Client disconnected or network error
			return err
		}
	}
	// Returning nil sends EOF to the client — stream is complete
	return nil
}
```

```go
// Client: receive a stream of products
func listProducts(client pb.ProductServiceClient, maxPrice float64) ([]*pb.Product, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	stream, err := client.ListProducts(ctx, &pb.ListProductsRequest{MaxPrice: maxPrice})
	if err != nil {
		return nil, fmt.Errorf("ListProducts: %w", err)
	}

	var products []*pb.Product
	for {
		p, err := stream.Recv()
		if err == io.EOF {
			break // server sent all products
		}
		if err != nil {
			return nil, fmt.Errorf("Recv: %w", err)
		}
		products = append(products, p)
	}
	return products, nil
}

func main() {
	// ... (connection setup same as unit 2)
	
	// Create some products first, then list filtered
	products, err := listProducts(client, 15.00) // only products under $15
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("found %d products under $15\n", len(products))
	for _, p := range products {
		fmt.Printf("  %s: $%.2f\n", p.Name, p.Price)
	}
}
```

## Exercise

**Build:** Add `ListProducts(filter) stream<Product>` to the proto and implement it on the server. The filter has a single field `max_price float64` — return all products if 0, otherwise only those below the price. Client collects the stream into a slice and prints the count.

**Input:** Create 5 products with prices 5, 10, 15, 20, 25. Call `ListProducts(max_price=16)`.

**Output:** 3 products returned (5, 10, 15).

**Acceptance:** Test with `bufconn`. Assert count=3 for max_price=16. Assert count=5 for max_price=0. Verify the server respects client cancellation (cancel context after receiving 2 items — server must not panic). Run `go test ./...`.

## Interview

- When would you use server streaming instead of pagination with `GET /products?page=N`?
- What does `stream.Recv()` return to signal the stream is complete?
- What happens on the server if you call `stream.Send()` after the client has cancelled the context?
