# Unit 3 — Cache-Aside Pattern Implementation

## Concept

Cache-aside means the application is responsible for both reading and writing the cache. On a cache miss, the application loads from the DB and then writes to the cache. The cache is never written to on updates — only invalidated. This is the right pattern when reads vastly outnumber writes and you can tolerate brief staleness. Cache degradation is required: if Redis is unavailable, the service must continue operating against the DB, with a warning logged.

## Code

```go
package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/example/app/domain"
)

type ProductService struct {
	repo  ProductRepository
	cache *redis.Client
	log   *slog.Logger
}

func (s *ProductService) GetProduct(ctx context.Context, id string) (*domain.Product, error) {
	key := productKey(id)

	// Try cache first
	data, err := s.cache.Get(ctx, key).Bytes()
	switch {
	case err == nil:
		// Cache hit — deserialize and return
		var p domain.Product
		if jsonErr := json.Unmarshal(data, &p); jsonErr != nil {
			s.log.WarnContext(ctx, "cache unmarshal failed", "key", key, "err", jsonErr)
			// Fall through to DB on corrupt cache data
		} else {
			return &p, nil
		}

	case errors.Is(err, redis.Nil):
		// Expected miss — load from DB

	default:
		// Redis is unhealthy — log warning, fall through to DB
		s.log.WarnContext(ctx, "redis unavailable, falling back to DB",
			"err", err, "key", key)
	}

	// Load from DB
	product, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// Populate cache — best-effort, never fail the request on cache write error
	if data, marshalErr := json.Marshal(product); marshalErr == nil {
		if setErr := s.cache.Set(ctx, key, data, 5*time.Minute).Err(); setErr != nil {
			s.log.WarnContext(ctx, "cache set failed", "key", key, "err", setErr)
		}
	}

	return product, nil
}

func productKey(id string) string {
	return fmt.Sprintf("product:v1:%s", id)
}
```

## Exercise

**Build:** The `ProductService.GetProduct` method with full cache degradation handling.
**Input:** Three scenarios to test: (1) Redis returns the value (cache hit), (2) Redis returns `redis.Nil` (miss, load DB), (3) Redis returns a connection error (degraded, load DB, log warning).
**Output:** All three scenarios return a product without error. Scenario 3 logs a warning. In scenarios 2 and 3, the repo is called exactly once.
**Acceptance:** Stop Redis locally, run your service — it still returns products from the DB. Restart Redis — it caches again on the next request. Verify by inspecting `KEYS product:*` in redis-cli after the second call.

## Interview

- What should happen to the request when Redis is completely unavailable?
- Why use a versioned key prefix like `product:v1:` instead of just `product:`?
- A cache write fails silently. Is that correct behavior? When would it not be?
