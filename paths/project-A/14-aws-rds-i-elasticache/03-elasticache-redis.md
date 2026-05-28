# 03 — ElastiCache Redis 7: Arhitektura i Integracija

## Redis vs Memcached: Zašto Redis

Za naš use case (session cache, potencijalno rate limiting, pub/sub za notifikacije):

| Feature | Redis 7 | Memcached |
|---|---|---|
| Persistence (RDB/AOF) | Da | Ne |
| Replication | Da | Ne (Memcached Cluster ne replicira) |
| Pub/Sub | Da | Ne |
| Data structures (sorted sets, streams) | Da | Ne |
| Cluster mode (sharding) | Da | Da |
| Lua scripting | Da | Ne |
| Multi-threading | Djelimično (I/O threads) | Da (multi-thread) |

**Jedini razlog za Memcached**: Pure caching workload s ekstremno visokim throughput-om gdje treba multi-threading. Za sve ostalo — Redis.

---

## Redis Cluster Mode vs Replication Group

### Redis Cluster Mode (sharding)

```
┌────────────┐   ┌────────────┐   ┌────────────┐
│ Shard 1    │   │ Shard 2    │   │ Shard 3    │
│ Primary    │   │ Primary    │   │ Primary    │
│ Replica    │   │ Replica    │   │ Replica    │
│ Slots 0-5k │   │ Slots 5k-10k│  │ Slots 10k-16k│
└────────────┘   └────────────┘   └────────────┘
```

- 16384 hash slotova raspoređenih po shardovima
- Horizontalno skaliranje write throughput-a
- Kompleksnija konfiguracija (client mora biti cluster-aware)
- Potrebno kada jedan Redis node nije dovoljan (>100k ops/sec, >100GB data)

### Replication Group (bez Cluster mode) — naš izbor

```
┌─────────────────────────────┐
│  Primary (AZ-a)             │
│  - Sve write operacije      │
│  - Read operacije           │
└─────────────┬───────────────┘
              │ async replication
              ▼
┌─────────────────────────────┐
│  Replica (AZ-b)             │
│  - Read operacije (opcionalno)│
│  - Automatic failover target│
└─────────────────────────────┘
```

**Zašto ovo za naš use case:**
- Session store — mali dataset (<1GB), ne treba sharding
- Throughput session operacija daleko ispod jednog Redis node-a kapaciteta
- Replica = HA (automatic failover ~30s vs Cluster mode ~10s ali uz kompleksnost)
- PHP i Go klijenti rade bez cluster-aware konfiguracije

---

## Terraform: ElastiCache Redis

### Subnet Group i Security Group

```hcl
# terraform/modules/elasticache/main.tf

resource "aws_elasticache_subnet_group" "redis" {
  name       = "project-a-${var.env_name}-redis"
  subnet_ids = var.private_subnet_ids

  tags = local.common_tags
}

resource "aws_security_group" "redis" {
  name        = "project-a-${var.env_name}-redis"
  description = "ElastiCache Redis access"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from EKS workers"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.eks_worker_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "project-a-${var.env_name}-redis-sg"
  })
}
```

### Auth Token u Secrets Manager

```hcl
resource "random_password" "redis_auth" {
  length  = 64
  special = false
  # Redis AUTH token: mora biti 16-128 karaktera, bez space i @ znakova
  # special = false je sigurno jer random_password default special characters
  # mogu uključivati @ koji je problem u nekim connection string formatima
}

resource "aws_secretsmanager_secret" "redis_auth" {
  name                    = "project-a-${var.env_name}/redis/auth"
  recovery_window_in_days = var.env_name == "prod" ? 30 : 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth.result
    host       = aws_elasticache_replication_group.redis.primary_endpoint_address
    port       = 6379
  })
}
```

### Replication Group

```hcl
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "project-a-${var.env_name}-redis"
  description          = "Redis session cache for ${var.env_name}"

  node_type            = var.node_type
  # dev: cache.t3.micro ($12/mj)
  # prod: cache.t3.small ili cache.r6g.large

  num_cache_clusters   = var.env_name == "prod" ? 2 : 1
  # prod: 2 = primary + 1 replica
  # dev/staging: 1 = samo primary (bez replice, bez HA)

  automatic_failover_enabled = var.env_name == "prod"
  # Automatic failover zahtijeva minimum 2 node-a
  # Kada primary failuje: replica postaje primary za ~30s

  multi_az_enabled = var.env_name == "prod"
  # Primary i replica u različitim AZ-ovima

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  # Security: in-transit i at-rest enkripcija
  at_rest_encryption_enabled  = true
  transit_encryption_enabled  = true
  auth_token                  = random_password.redis_auth.result
  # auth_token zahtijeva transit_encryption_enabled = true

  engine_version = "7.0"

  parameter_group_name = aws_elasticache_parameter_group.redis7.name

  maintenance_window = "sun:05:00-sun:06:00"
  snapshot_window    = "03:00-04:00"

  snapshot_retention_limit = var.env_name == "prod" ? 7 : 1
  # RDB snapshots: prod 7 dana, dev 1 dan
  # Ovo NIJE zamjena za aplikativni backup sessiona
  # Korisno za: vraćanje Redis state-a za debugging, ili za load testing

  apply_immediately = var.env_name != "prod"

  # Notification za failover eventi
  notification_topic_arn = var.sns_topic_arn

  tags = local.common_tags

  lifecycle {
    ignore_changes = [num_cache_clusters]
    # ElastiCache može automatski dodati/ukloniti replice — ignoriraj te promjene
  }
}

resource "aws_elasticache_parameter_group" "redis7" {
  family = "redis7"
  name   = "project-a-${var.env_name}-redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
    # Za session cache: allkeys-lru
    # Kada Redis dostigne maxmemory, izbacuje najstarije korištene ključeve
    # Alternativa za čisti cache (ne session): volatile-lru (samo ključevi s TTL)
    # NIKAD noeviction za session store — Redis bi počeo vraćati OOM greške
  }

  parameter {
    name  = "maxmemory-samples"
    value = "10"
    # LRU aproksimacija: koliko ključeva uzorkuje pri eviction
    # Viši = precizniji LRU, ali sporiji. 10 je dobar balans.
  }

  parameter {
    name  = "timeout"
    value = "300"
    # Idle connection timeout u sekundama
    # PHP/Go klijenti trebaju reconnect logiku
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  tags = local.common_tags
}
```

### Outputs

```hcl
output "primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "reader_endpoint" {
  # Reader endpoint load-balancira read operacije po svim replikama
  value = aws_elasticache_replication_group.redis.reader_endpoint_address
}

output "auth_secret_arn" {
  value = aws_secretsmanager_secret.redis_auth.arn
}
```

---

## PHP Session Handler Konfiguracija

### Native PHP Redis Session Handler

PHP `ext-redis` session handler je najperformantniji (C extension, ne PHP userland).

```ini
; php/config/session.ini (mounted kao ConfigMap u K8s)

session.save_handler = redis
session.save_path = "tls://redis-endpoint:6379?auth=AUTH_TOKEN&database=0&timeout=2.5&read_timeout=2.5&retry_interval=100&persistent=1"
; tls:// protokol za transit_encryption_enabled = true

session.gc_maxlifetime = 3600
; Session TTL u sekundama (1h)
; Redis automatski briše ključeve nakon ovog perioda (EXPIRE se postavlja pri SET)

session.cookie_lifetime = 0
; Browser session (briše se pri zatvaranju) vs persistent
; Za produkciju: 0 (browser session) + server-side TTL

session.cookie_secure = 1
session.cookie_httponly = 1
session.cookie_samesite = "Strict"
; Sve tri opcije su obavezne za sigurnost sessiona
```

**Napomena o `persistent=1`**: Konekcija se ne zatvara na kraju PHP request-a nego ostaje u FPM worker procesu. Ovo je ispravno ponašanje za session handler. Bez `persistent=1`, svaki PHP request otvara novu Redis konekciju.

### PHP-FPM Pool konfiguracija (za Redis konekcije)

```ini
; php/config/www.conf
pm = dynamic
pm.max_children = 20
pm.start_servers = 5

; 20 FPM workers × 1 Redis konekcija po worker-u = 20 konekcija
; Mora biti unutar ElastiCache default maxclients = 65000
```

---

## Go Redis Client

### Setup s go-redis/v9

```go
// internal/cache/redis.go
package cache

import (
    "context"
    "crypto/tls"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"
)

type RedisClient struct {
    client *redis.Client
}

func NewRedisClient(cfg RedisConfig) (*RedisClient, error) {
    opts := &redis.Options{
        Addr:     fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
        Password: cfg.AuthToken,
        DB:       0,

        // TLS za ElastiCache transit_encryption_enabled = true
        TLSConfig: &tls.Config{
            MinVersion: tls.VersionTLS12,
        },

        // Connection pool
        PoolSize:     10,   // Max konekcija u poolu (per Go instance)
        MinIdleConns: 3,    // Drži minimum ovih konekcija otvorenim
        MaxIdleConns: 5,

        // Timeouts
        DialTimeout:  5 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,

        // Retry — važno za ElastiCache failover scenarij
        MaxRetries:      3,
        MinRetryBackoff: 8 * time.Millisecond,
        MaxRetryBackoff: 512 * time.Millisecond,
        // Exponential backoff: 8ms, 16ms, 32ms... do 512ms

        // Pool health
        ConnMaxLifetime: 5 * time.Minute,
        ConnMaxIdleTime: 2 * time.Minute,
        // Sprječava "stale connection" problem koji se javlja nakon ElastiCache maintenance
    }

    client := redis.NewClient(opts)

    // Provjeri konekciju pri startu
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if err := client.Ping(ctx).Err(); err != nil {
        return nil, fmt.Errorf("redis ping failed: %w", err)
    }

    return &RedisClient{client: client}, nil
}

// Session operacije (example)
func (r *RedisClient) SetSession(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    return r.client.Set(ctx, "session:"+key, value, ttl).Err()
}

func (r *RedisClient) GetSession(ctx context.Context, key string) (string, error) {
    return r.client.Get(ctx, "session:"+key).Result()
}

func (r *RedisClient) DeleteSession(ctx context.Context, key string) error {
    return r.client.Del(ctx, "session:"+key).Err()
}

// Health check za /health endpoint
func (r *RedisClient) Ping(ctx context.Context) error {
    return r.client.Ping(ctx).Err()
}
```

### Retry politika — zašto je bitna

ElastiCache automatic failover traje ~30 sekundi. Za to vrijeme:

1. Primary pada
2. ElastiCache detectira (health check interval ~10s)
3. Promocija replike u primary (~15-20s)
4. DNS update za primary endpoint (~10s propagacija)

Go klijent s `MaxRetries = 3` i exponential backoff može "preživjeti" kratke prekide bez da vraća grešku korisniku, ako su retries dovoljno česti (ukupno ~1.5s retry window je premalo za 30s failover).

**Realističan pristup**: Circuit breaker pattern ili graceful degradation (vidi sekciju Failure Mode).

---

## Failure Mode: Šta se Desi Kada Redis Padne

### Scenarij 1: Planned maintenance (ElastiCache restart)

- Multi-node: automatic failover, ~30s downtime na primary endpointu
- Single node (dev): Redis nedostupan ~5-10 minuta

### Scenarij 2: AZ outage

- Primary i replica u različitim AZ-ovima → replica postaje primary automatski
- DNS propagacija: primary endpoint adresa se mijenja

### Posljedice za aplikaciju

**PHP session handler** — direktno gubi session podatke:
- Korisnik dobija nova prazna sesija = logout
- Ne možeš "retry" session write kada Redis ne odgovara

**Go service** — Redis error propagira se kao 5xx ako nema fallback-a

### Fallback strategija za PHP

```php
// config/session_handler.php

$redisAvailable = @fsockopen($redisHost, 6379, $errno, $errstr, 1);
if ($redisAvailable) {
    ini_set('session.save_handler', 'redis');
    ini_set('session.save_path', $redisDsn);
} else {
    // Fallback na file-based sessions
    ini_set('session.save_handler', 'files');
    ini_set('session.save_path', '/tmp/sessions');
    // Loguj incident
    error_log("Redis unavailable, falling back to file sessions");
}
session_start();
```

**Bolje rješenje**: Kubernetes readiness probe za PHP pod koji provjerava Redis dostupnost. Ako Redis nije dostupan, PHP pod se izbaci iz Service endpointova i load balancer prestaje slati traffic → fail-fast umjesto degraded state.

### Fallback strategija za Go service

```go
// Graceful degradation za non-critical caching
func (s *Service) GetProductWithCache(ctx context.Context, id int) (*Product, error) {
    // Pokušaj dohvatiti iz cache-a
    if cached, err := s.redis.Get(ctx, fmt.Sprintf("product:%d", id)); err == nil {
        var product Product
        json.Unmarshal([]byte(cached), &product)
        return &product, nil
    }

    // Redis nedostupan ili cache miss → idi u bazu
    product, err := s.db.GetProduct(ctx, id)
    if err != nil {
        return nil, err
    }

    // Pokušaj cachirati (ignoriraj grešku ako Redis ne radi)
    if data, err := json.Marshal(product); err == nil {
        _ = s.redis.Set(ctx, fmt.Sprintf("product:%d", id), data, 5*time.Minute)
    }

    return product, nil
}
```

**Session loss je neizbjezna** kada Redis padne bez replike. Prihvatljivo za dev/staging, ali za prod:
- Minimum: primary + 1 replica u drugom AZ-u
- Production SLA zahtijeva Multi-AZ + automatic failover konfiguraciju

### ElastiCache Failover vremena po konfiguraciji

| Konfiguracija | Failover trajanje |
|---|---|
| Single node (bez replike) | 5-10 min (nova instanca) |
| Multi-AZ, automatic failover | 30-60s |
| Redis Cluster mode | 10-30s (per shard) |
