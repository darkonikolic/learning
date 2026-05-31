# 06 — NATS JetStream

## Kada Redis Streams nije dovoljan

Redis Streams koje koristimo u project-A su odlično rješenje za interne workloade u okviru jedne aplikacije. Ali postoje scenariji gdje je potrebno više:

| Scenarij | Redis Streams | NATS JetStream |
|----------|--------------|----------------|
| Poruke unutar jedne aplikacije | Odlično | Overkill |
| Multi-tenant SaaS, više servisa | Funkcionira | Bolji fit |
| Replay starih poruka | Da (XRANGE) | Da |
| Garantovana isporuka (ACK) | Da | Da |
| Cross-cluster (više datacentara) | Složeno | Ugrađeno |
| Throughput 1M+ msg/s | Ograničeno | Optimizirano |
| Kafka migracija | — | Lakša od Kafka |
| Operativna složenost | Niska (Redis već imaš) | Niska (single binary) |

NATS JetStream je middle ground između Redis Streams i Kafke: viši throughput od Redis-a, daleko manji operativni overhead od Kafke.

---

## Arhitektura NATS

```
Publisher                 NATS Server              Consumer
  │                          │                        │
  │  Publish("orders.new")   │                        │
  ├─────────────────────────▶│                        │
  │                          │  Store u JetStream     │
  │                          │  (subject: orders.new) │
  │                          │──────────────────────▶ │
  │                          │                        │ Process
  │                          │◀────────────────────── │ ACK
  │                          │                        │
```

Subject je hierarchical path: `orders.new`, `orders.paid`, `orders.>` (wildcard za sve orders).

---

## Instalacija u Kubernetes

```yaml
# nats-values.yaml (Helm)
nats:
  jetstream:
    enabled: true
    fileStorage:
      enabled: true
      size: 10Gi
      storageClassName: gp3
  cluster:
    enabled: true  # 3 replika za produkciju
    replicas: 3
```

```bash
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm install nats nats/nats \
  --namespace messaging \
  --create-namespace \
  -f nats-values.yaml
```

Za development: single server bez persistence je dovoljan.

---

## Go publisher

```go
import (
    "github.com/nats-io/nats.go"
    "github.com/nats-io/nats.go/jetstream"
)

type EventPublisher struct {
    js jetstream.JetStream
}

func NewEventPublisher(natsURL string) (*EventPublisher, error) {
    nc, err := nats.Connect(natsURL,
        nats.RetryOnFailedConnect(true),
        nats.MaxReconnects(-1),  // beskonačni reconnect
        nats.ReconnectWait(2*time.Second),
    )
    if err != nil {
        return nil, err
    }

    js, err := jetstream.New(nc)
    if err != nil {
        return nil, err
    }

    // Kreira stream ako ne postoji
    _, err = js.CreateOrUpdateStream(context.Background(), jetstream.StreamConfig{
        Name:     "ORDERS",
        Subjects: []string{"orders.>"},  // sve orders.*
        Storage:  jetstream.FileStorage,
        Replicas: 3,
        MaxAge:   7 * 24 * time.Hour,  // retencija 7 dana
    })
    if err != nil {
        return nil, err
    }

    return &EventPublisher{js: js}, nil
}

func (p *EventPublisher) PublishOrderCreated(ctx context.Context, order *Order) error {
    payload, err := json.Marshal(OrderCreatedEvent{
        OrderID:    order.ID,
        UserID:     order.UserID,
        Amount:     order.Amount,
        OccurredAt: time.Now().UTC(),
    })
    if err != nil {
        return err
    }

    // PublishAsync za visoki throughput, Publish za garantovanu isporuku
    ack, err := p.js.Publish(ctx, "orders.created", payload,
        jetstream.WithMsgID(order.ID),  // deduplication — isti ID neće biti duplo pohranjen
    )
    if err != nil {
        return fmt.Errorf("publish order.created: %w", err)
    }

    _ = ack  // možeš potvrditi sequence number ili stream
    return nil
}
```

---

## Go consumer — push i pull

### Push consumer (server šalje poruke)

```go
func (s *InventoryService) StartConsumer(ctx context.Context) error {
    cons, err := s.js.CreateOrUpdateConsumer(ctx, "ORDERS", jetstream.ConsumerConfig{
        Durable:       "inventory-service",  // trajni consumer — pamti offset
        AckPolicy:     jetstream.AckExplicitPolicy,
        FilterSubject: "orders.created",
        MaxDeliver:    5,  // max retry
        AckWait:       30 * time.Second,
    })
    if err != nil {
        return err
    }

    // ConsumeCont — kontinuirano prima poruke
    consCtx, err := cons.Consume(func(msg jetstream.Msg) {
        if err := s.handleOrderCreated(ctx, msg.Data()); err != nil {
            s.logger.Error("handle failed", "err", err)
            msg.NakWithDelay(5 * time.Second)  // retry nakon 5s
            return
        }
        msg.Ack()
    })
    if err != nil {
        return err
    }
    defer consCtx.Stop()

    <-ctx.Done()
    return nil
}
```

### Pull consumer (sam povlačiš)

```go
// Bolje za batch obradu ili kada hoćeš kontrolu nad brzinom
func (s *InventoryService) ProcessBatch(ctx context.Context) error {
    msgs, err := s.consumer.Fetch(100,
        jetstream.FetchMaxWait(1*time.Second),
    )
    if err != nil {
        return err
    }

    for msg := range msgs.Messages() {
        if err := s.handleOrderCreated(ctx, msg.Data()); err != nil {
            msg.NakWithDelay(5 * time.Second)
            continue
        }
        msg.Ack()
    }
    return msgs.Error()
}
```

---

## Key-Value store — kao Redis, ali repliciran

NATS JetStream ima ugrađen KV store koji se automatski replicira:

```go
kv, err := js.CreateOrUpdateKeyValue(ctx, jetstream.KeyValueConfig{
    Bucket:   "feature-flags",
    Replicas: 3,
    TTL:      24 * time.Hour,
})

// Pisanje
kv.Put(ctx, "checkout.new-flow", []byte("true"))

// Čitanje
entry, _ := kv.Get(ctx, "checkout.new-flow")
fmt.Println(string(entry.Value()))

// Watch — dobij notifikaciju na promjenu (config hot reload)
watcher, _ := kv.Watch(ctx, "feature-flags.>")
for update := range watcher.Updates() {
    if update == nil {
        continue  // initial state completed
    }
    reloadFeatureFlag(update.Key(), update.Value())
}
```

---

## NATS vs Kafka — zašto ne Kafka

Kafka je industrijski standard za visoki throughput (milijuni poruka/s), ali za project-A:

| | NATS JetStream | Kafka |
|--|----------------|-------|
| Operativni overhead | Nizak (single binary) | Visok (Zookeeper/KRaft + brokers) |
| Latency | Sub-millisecond | 5-15ms |
| Učenje | 1-2 dana | 1-2 tjedna |
| K8s deployment | Jedan Helm chart | Strimzi operator, planning |
| Replay starih poruka | Da | Da |
| Throughput | ~10M msg/s | ~100M msg/s |
| Kada koristiti | Do 10M msg/s, interne poruke | 10M+ msg/s, log aggregation, analytics |

Za project-A: NATS JetStream. Kafka je ispravan izbor kada prelazite 10M poruka/s ili trebate multi-datacenter replikaciju s garantovanim redoslijedom.

---

## Veza sa project-A

Migracija sa Redis Streams na NATS:

```
Prije (Redis Streams):
  go-service XADD events:orders → consumer XREADGROUP

Poslije (NATS JetStream):
  go-service Publish("orders.created") → consumer Consume()
```

Interface ostaje isti — samo implementacija se mijenja. Zato ima smisla definirati interface u go-service od početka:

```go
type EventBus interface {
    Publish(ctx context.Context, subject string, payload []byte) error
    Subscribe(ctx context.Context, subject string, handler func([]byte) error) error
}

// RedisStreamsBus implementira EventBus — za project-A sada
// NatsJetStreamBus implementira EventBus — za skaliranje poslije
```
