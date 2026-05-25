# Quick Reference — Redis & Caching

## go-redis v9 basics
rdb := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
rdb.Set(ctx, key, value, ttl)
val, err := rdb.Get(ctx, key).Result()
errors.Is(err, redis.Nil)  // cache miss check

## Common commands
rdb.Del(ctx, key)
rdb.Exists(ctx, key)
rdb.Expire(ctx, key, ttl)
rdb.Incr(ctx, key)
rdb.HSet(ctx, key, field, value)
rdb.HGet(ctx, key, field)

## Pipeline (batch, 1 RTT)
pipe := rdb.Pipeline()
pipe.Set(ctx, "a", 1, time.Minute)
cmds, _ := pipe.Exec(ctx)

## Cache-aside flow
1. GET from cache → hit: return
2. miss: load from DB
3. SET in cache with TTL
4. return

## Stampede prevention
singleflight.Group — collapses concurrent misses to 1 DB call

## TTL discipline
- User sessions: 30min–24h
- Reference data: 5–15min
- Rate limit counters: 1min exact
- Never: no TTL on mutable data
