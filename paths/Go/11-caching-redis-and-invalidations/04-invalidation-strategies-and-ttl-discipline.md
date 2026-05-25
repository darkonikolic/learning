# Unit 4 — Invalidation Strategies and TTL Discipline

## Concept

Delete-on-write is the simplest correct invalidation: when you update an entity, delete its cache key. The next read repopulates from the DB. Never update the cache on write — that creates race conditions between writers. Stampede prevention solves a different problem: when a popular key expires, many goroutines miss simultaneously and all try to load from the DB. `singleflight.Group` ensures only one goroutine does the DB fetch while the rest wait and reuse the result.

## Code

```go
package service

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"golang.org/x/sync/singleflight"
	"github.com/redis/go-redis/v9"
	"github.com/example/app/domain"
)

type UserService struct {
	repo  UserRepository
	cache *redis.Client
	sf    singleflight.Group
}

// UpdateUser updates the DB and deletes the cache key.
func (s *UserService) UpdateUser(ctx context.Context, u *domain.User) error {
	if err := s.repo.Update(ctx, u); err != nil {
		return err
	}
	// Delete-on-write — never update the cache here
	s.cache.Del(ctx, userKey(u.ID))
	return nil
}

// GetUser uses singleflight to prevent cache stampede.
func (s *UserService) GetUser(ctx context.Context, id string) (*domain.User, error) {
	key := userKey(id)

	// Check cache first (outside singleflight — fast path)
	if data, err := s.cache.Get(ctx, key).Bytes(); err == nil {
		var u domain.User
		if json.Unmarshal(data, &u) == nil {
			return &u, nil
		}
	}

	// singleflight: only one goroutine loads from DB for this key at a time
	v, err, _ := s.sf.Do(key, func() (interface{}, error) {
		u, err := s.repo.FindByID(ctx, id)
		if err != nil {
			return nil, err
		}
		data, _ := json.Marshal(u)
		s.cache.Set(ctx, key, data, 10*time.Minute)
		return u, nil
	})
	if err != nil {
		return nil, err
	}
	return v.(*domain.User), nil
}

func userKey(id string) string {
	return fmt.Sprintf("user:v1:%s", id)
}
```

## Exercise

**Build:** A stampede simulation with and without singleflight.
**Input:** A `UserService.GetUser` with a mock repo. Simulate a cache miss for `user:1`. Launch 10 goroutines concurrently, all calling `GetUser("user:1")`.
**Output:** Without singleflight: repo `FindByID` is called 10 times (observe with a counter). With singleflight: repo `FindByID` is called exactly 1 time. All 10 callers receive the correct result.
**Acceptance:** Use an `atomic.Int64` counter on the mock repo to count calls. Without singleflight: counter >= 2 (likely 10). With singleflight: counter == 1. Run the test with `-race` — no data races.

## Interview

- Why delete the cache key on write instead of updating it?
- What is a cache stampede and why does it happen exactly when you least want it (high traffic + cold cache)?
- What does the third return value from `singleflight.Do` tell you, and when does it matter?
