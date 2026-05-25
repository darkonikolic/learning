# Unit 2 — go-redis Client Patterns

## Concept

`go-redis/v9` is the standard Redis client for Go. Always configure pool size and connection timeouts explicitly — the defaults are too permissive for production. `redis.Nil` is returned from `Get` when a key does not exist — it is not an error, it is a miss, and you must handle it separately from actual errors. Pipelines batch multiple commands into one round trip, which matters when you are setting 10 keys at once.

## Code

```go
package cache

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

func NewClient(addr string) *redis.Client {
	return redis.NewClient(&redis.Options{
		Addr:         addr,
		PoolSize:     20,              // max connections in pool
		MinIdleConns: 5,               // keep warm
		DialTimeout:  2 * time.Second,
		ReadTimeout:  1 * time.Second,
		WriteTimeout: 1 * time.Second,
	})
}

// Get returns the value, ErrMiss if key does not exist, or an error.
var ErrMiss = errors.New("cache miss")

func Get(ctx context.Context, rdb *redis.Client, key string) ([]byte, error) {
	val, err := rdb.Get(ctx, key).Bytes()
	if errors.Is(err, redis.Nil) {
		return nil, ErrMiss // not an error — key does not exist
	}
	return val, err
}

// Set stores a value with a mandatory TTL.
func Set(ctx context.Context, rdb *redis.Client, key string, val []byte, ttl time.Duration) error {
	if ttl <= 0 {
		return errors.New("ttl must be positive — never cache without expiry")
	}
	return rdb.Set(ctx, key, val, ttl).Err()
}

// Pipeline: set multiple keys in one round trip.
func BulkSet(ctx context.Context, rdb *redis.Client, pairs map[string][]byte, ttl time.Duration) error {
	pipe := rdb.Pipeline()
	for k, v := range pairs {
		pipe.Set(ctx, k, v, ttl)
	}
	cmds, err := pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("pipeline exec: %w", err)
	}
	for _, cmd := range cmds {
		if cmd.Err() != nil {
			return fmt.Errorf("pipeline cmd %s: %w", cmd.Name(), cmd.Err())
		}
	}
	return nil
}
```

## Exercise

**Build:** A Redis-backed rate limiter: `Allow(ctx, userID string) (bool, error)`.
**Input:** Each call increments a counter for the user. Limit: 5 requests per 10 seconds. On the first increment, set a 10-second expiry.
**Output:** `Allow` returns `true` if under limit, `false` if over. Uses `INCR` and `EXPIRE` commands. The EXPIRE is only set when the key is new (count == 1) to avoid resetting the window on every call.
**Acceptance:** Call `Allow` 6 times for the same user. First 5 return true. Sixth returns false. Wait for TTL to expire (or manually delete the key), call again — returns true. Test with `redis.NewClient` pointing at a local Redis instance.

## Interview

- What does `redis.Nil` mean, and why do you handle it separately from other errors?
- Why set `PoolSize` explicitly instead of using the default?
- Why must `EXPIRE` only be called when the counter is 1 (new key) in a rate limiter?
