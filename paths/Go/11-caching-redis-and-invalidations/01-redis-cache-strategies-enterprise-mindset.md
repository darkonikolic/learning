# Unit 1 — Redis Cache Strategies

## Concept

Cache-aside is the most common pattern: check the cache, on a miss load from DB, then populate the cache. The application owns the cache interaction. Write-through writes to both cache and DB on every update — cache is never stale but writes are slower. Cache-only is rare and only appropriate when data loss is acceptable. TTLs are mandatory on every key — caching without expiry creates stale data that lives forever and corrupts production reads.

## Code

```go
package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/example/app/domain"
)

const productTTL = 5 * time.Minute

type ProductService struct {
	repo  ProductRepository
	cache *redis.Client
}

// Cache-aside: check cache → miss → load DB → populate cache
func (s *ProductService) GetProduct(ctx context.Context, id string) (*domain.Product, error) {
	key := fmt.Sprintf("product:%s", id)

	// 1. Check cache
	data, err := s.cache.Get(ctx, key).Bytes()
	if err == nil {
		var p domain.Product
		if err := json.Unmarshal(data, &p); err == nil {
			return &p, nil // cache hit
		}
	}
	if !errors.Is(err, redis.Nil) {
		// Redis error — log and fall through to DB (degraded mode)
		fmt.Printf("cache get error: %v\n", err)
	}

	// 2. Cache miss — load from DB
	product, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// 3. Populate cache — always with TTL
	if data, err := json.Marshal(product); err == nil {
		s.cache.Set(ctx, key, data, productTTL) // best-effort, ignore error
	}

	return product, nil
}

// Write-through: update DB and cache together
func (s *ProductService) UpdateProduct(ctx context.Context, p *domain.Product) error {
	if err := s.repo.Update(ctx, p); err != nil {
		return err
	}
	key := fmt.Sprintf("product:%s", p.ID)
	data, _ := json.Marshal(p)
	return s.cache.Set(ctx, key, data, productTTL).Err()
}
```

## Exercise

**Build:** Cache-aside for `ProductService.GetProduct` using a mock repository and a mock Redis client.
**Input:** Call `GetProduct` twice with the same product ID.
**Output:** First call: repo `FindByID` is called once, result stored in cache. Second call: repo `FindByID` is NOT called (cache hit).
**Acceptance:** Use a counter on the mock repo to verify call count. First call count=1, second call count=1 (unchanged). Add a test where Redis returns an error — verify the service falls through to the DB and does not return an error to the caller.

## Interview

- What is the difference between cache-aside and write-through in terms of who controls cache population?
- A cache key has no TTL. What happens over time in production?
- Why is "fall through to DB on Redis error" the correct behavior instead of returning an error?
