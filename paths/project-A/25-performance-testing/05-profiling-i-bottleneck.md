# 05 — Profiling i Bottleneck analiza

## Go pprof — CPU i memory profiling

Go ima ugrađen HTTP profiler. Jedino što trebaš je importati ga:

```go
// cmd/server/main.go ili internal/server/server.go
import (
    "net/http"
    _ "net/http/pprof"   // blank import registruje /debug/pprof/* handlere
    "log"
)

func main() {
    // Pokreni pprof server na posebnom portu (NE na production API portu)
    go func() {
        log.Println("pprof listening on :6060")
        log.Fatal(http.ListenAndServe(":6060", nil))
    }()

    // ... ostali startup kod ...
}
```

```yaml
# kubernetes/go-service/deployment.yaml — expose pprof port
spec:
  containers:
    - name: go-service
      ports:
        - containerPort: 8080   # API
        - containerPort: 6060   # pprof (interno samo!)
      env:
        - name: PPROF_ENABLED
          value: "true"   # samo u dev/staging
```

**NIKAD ne expose pprof u production bez autentifikacije** — daje stack traces i memory dump svakome.

---

## CPU profiling tokom k6 load testa

Pokretaš pprof profiling dok k6 tест tece — to je jedini način da uhvatiš pravi CPU bottleneck.

```bash
# Terminal 1: pokreni k6 load test
docker run --rm -i \
  -e BASE_URL=https://app.staging.firma.com \
  grafana/k6:0.49.0 run - < tests/performance/load-test.js &

# Terminal 2: uhvati CPU profile dok test tece
kubectl port-forward pod/go-service-xxx 6060:6060 -n project-a-staging &

# 30-sekundni CPU profile — snima TOKOM opterećenja
go tool pprof -http=:8081 "http://localhost:6060/debug/pprof/profile?seconds=30"
# Otvara browser s flame graph-om

# Alternativno, spremi profile file:
curl -o cpu.prof "http://localhost:6060/debug/pprof/profile?seconds=30"
go tool pprof -http=:8081 cpu.prof
```

**Čitanje flame graph-a:**

```
Širina bar-a = % CPU vremena potrošenog u toj funkciji
Visina = call stack depth

Tražiš: Široke barove pri vrhu (leaf functions) = gdje se gubi CPU

Primjer čestih nalaza:
  - json.Marshal/json.Unmarshal — previše serijalizacije, cache-aj
  - database/sql.(*Stmt).QueryContext — N+1 query problem
  - regexp.Match — compile RegExp van handler-a (jednom, ne per-request)
  - crypto/tls — ako nema TLS session resumption
```

---

## Goroutine profiling — otkrivanje leakova

```bash
# Trenutni goroutine snapshot
curl "http://localhost:6060/debug/pprof/goroutine?debug=1"

# Prati rast kroz vrijeme:
while true; do
  COUNT=$(curl -s "http://localhost:6060/debug/pprof/goroutine?debug=1" | head -1 | grep -oP '\d+')
  echo "$(date): goroutines = $COUNT"
  sleep 60
done
```

**Goroutine leak primjer:**

```go
// BUG: leak — goroutina čeka na channel koji nikad ne dobija podatke
func handleRequest(ctx context.Context) {
    resultCh := make(chan Result)
    go func() {
        result := db.Query(...)   // Što ako ctx cancela? Goroutina ostaje zauvijek
        resultCh <- result
    }()
    
    select {
    case result := <-resultCh:
        return result
    case <-ctx.Done():
        return nil   // goroutina još uvijek živi!
    }
}

// FIX: proslijedi ctx u goroutinu
func handleRequest(ctx context.Context) {
    resultCh := make(chan Result, 1)   // buffered — goroutina može exit bez blockinga
    go func() {
        result, err := db.QueryContext(ctx, ...)   // ctx cancelation ubija query
        if err != nil {
            return   // ctx done — goroutina čisto exituje
        }
        resultCh <- result
    }()
    
    select {
    case result := <-resultCh:
        return result
    case <-ctx.Done():
        return nil
    }
}
```

---

## Memory profiling

```bash
# Heap profile — trenutno stanje memorije
curl -o heap.prof "http://localhost:6060/debug/pprof/heap"
go tool pprof -http=:8081 heap.prof

# Allocation profiling — što se najviše alocira
curl -o alloc.prof "http://localhost:6060/debug/pprof/allocs"
go tool pprof -http=:8081 alloc.prof
```

**Tražiš u heap profiler:**
```
inuse_objects: objekti koji su trenutno u memoriji
alloc_objects: ukupno alocirani (+ garbage collected)

Visok inuse_objects na jednoj lokaciji → potencijalni leak ili prevelik cache
```

---

## MySQL slow query analiza

```bash
# 1. Provjeri da li je slow query log omogućen
kubectl exec -n project-a-dev mysql-0 -- \
  mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SHOW VARIABLES LIKE 'slow_query_log%';"

# Ako nije: (u dev/staging — ne diraji production bez procedure)
kubectl exec -n project-a-dev mysql-0 -- \
  mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SET GLOBAL slow_query_log = ON;
      SET GLOBAL long_query_time = 0.5;
      SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';"

# 2. Kopiraj slow log na local
kubectl cp project-a-dev/mysql-0:/var/log/mysql/slow.log ./slow.log

# 3. Analiziraj s pt-query-digest
docker run --rm \
  -v ./slow.log:/slow.log \
  percona/percona-toolkit:3.5.5 \
  pt-query-digest /slow.log | head -100
```

**Čitanje pt-query-digest output-a:**

```
# Profile
# Rank Query ID           Response time   Calls R/Call  V/M   Item
# ==== ================== =============== ===== ======= ===== ====
#    1 0xABC123...         45.2321 61.2%    234  0.1932  0.40  SELECT users
#    2 0xDEF456...         12.3456 16.7%   1823  0.0068  0.12  SELECT orders

Rank 1: Query koristi 61% ukupnog slow log vremena
→ Pogledaj EXPLAIN za tu query
→ Obično: nedostaje index, full table scan, ili N+1

kubectl exec mysql-0 -- mysql -e "EXPLAIN SELECT * FROM users WHERE email = 'x';"
# type = ALL → full table scan → dodaj index
# type = ref → koristi index (dobro)
```

---

## PHP-FPM status monitoring

```bash
# PHP-FPM status mora biti konfigurisan u php-fpm.conf:
# pm.status_path = /fpm-status

# Provjeri workers:
kubectl exec -n project-a-dev \
  $(kubectl get pod -n project-a-dev -l app=php-service -o name | head -1) \
  -- curl -s http://localhost/fpm-status?full

# Output koji tražiš:
# pool: www
# process manager: dynamic
# start time: 27/May/2026:10:00:00 +0000
# accepted conn: 12453
# listen queue: 0          ← > 0 znači workers su puni, requests čekaju
# max listen queue: 0
# listen queue len: 128
# idle processes: 8
# active processes: 2
# total processes: 10
# max active processes: 8  ← blizu max_children? Problem.
# max children reached: 3  ← koliko puta smo HIT max workers
```

**Kad `max children reached` raste brzo tokom load testa:**

```bash
# Provjeri pm.max_children u php-fpm.d/www.conf
kubectl exec php-service-xxx -- php-fpm -tt 2>&1 | grep max_children

# Računanje optimalnog max_children:
# max_children = (dostupna RAM - OS overhead) / prosječna PHP worker veličina
# Primjer: (2GB - 512MB) / 64MB per worker = 24 workers

# Za emergency fix (ne restart):
kubectl exec php-service-xxx -- kill -USR2 1   # graceful reload PHP-FPM config
```

---

## Redis profiling

```bash
# Ukupno stanje
kubectl exec -n project-a-dev redis-0 -- redis-cli INFO all

# Memorija
kubectl exec -n project-a-dev redis-0 -- redis-cli INFO memory
# Tražiš:
# used_memory_human: 234.56M    ← trenutna upotreba
# mem_fragmentation_ratio: 1.2  ← > 1.5 = fragmentacija, prestaruj Redis
# maxmemory_policy: allkeys-lru ← da li ima policy? Bez njega → OOM

# MEMORY DOCTOR — automatska dijagnoza
kubectl exec -n project-a-dev redis-0 -- redis-cli MEMORY DOCTOR
# Tipični output:
# "Sam, I detected a few memory issues with your instance:
#  * Peak memory: 1.23G, current: 234M -- memory usage decreased by a lot"
# → OK, to je normalno nakon expiry

# Slow log — Redis komande koje traju dugo
kubectl exec -n project-a-dev redis-0 -- redis-cli SLOWLOG GET 10
# FORMAT: [ID, timestamp, microseconds, command, args]
# Ako vidiš KEYS * → nikad ne koristiti u production (blokira)
# Ako vidiš SMEMBERS na veliku listu → razmisli o paginaciji

# Keyspace statistike — koliko ključeva, TTL distribucija
kubectl exec -n project-a-dev redis-0 -- redis-cli INFO keyspace
# db0:keys=23456,expires=23100,avg_ttl=3600000
# expires ≈ keys → dobro, ključevi imaju TTL
# expires << keys → memorija raste zauvijek
```

---

## Sistemski pogled — kombinacija svih alata

Workflow kad nađeš visoku latency u k6 rezultatima:

```
1. k6 output: p95 = 650ms (SLO: < 500ms)
   → http_req_waiting visok → problem je server, ne network

2. kubectl top pods -n project-a-staging --sort-by=cpu
   → go-service: 850m CPU (request: 500m, limit: 1000m)
   → go-service je CPU throttled!

3. kubectl describe hpa go-service-hpa -n project-a-staging
   → Current replicas: 2, Desired: 4
   → Scale-up je u toku (kasni 2 minute)

4. go tool pprof (CPU profile tokom testa)
   → 42% vremena u json.Marshal
   → API vraća prevelike JSON response-e bez paginacije

5. Akcija:
   a. Kratkoročno: povećaj minReplicas na 4 u HPA
   b. Dugoročno: dodaj paginaciju, smanjuj JSON payload
   c. Provjeri: dodaj response caching u Redis za heavy endpointe
```

```bash
# Alati koje vidiš u jednom terminalu za monitoring tokom k6 testa:

# Split terminal setup:
# Panel 1: kubectl top
watch -n 2 'kubectl top pods -n project-a-staging --sort-by=cpu'

# Panel 2: Go goroutines
watch -n 5 'curl -s http://localhost:6060/debug/pprof/goroutine?debug=1 | head -3'

# Panel 3: MySQL connections
watch -n 2 'kubectl exec mysql-0 -- mysql -u root -p"$PASS" -e "SHOW STATUS LIKE \"Threads_connected\";"'

# Panel 4: Redis memory
watch -n 5 'kubectl exec redis-0 -- redis-cli INFO memory | grep used_memory_human'
```
