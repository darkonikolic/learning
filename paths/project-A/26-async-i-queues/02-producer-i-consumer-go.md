# 02 — Producer i Consumer (Go)

## Producer — Go API service

```go
package queue

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type EmailEvent struct {
	Type      string `json:"type"`             // "verify", "reset_password", "welcome"
	To        string `json:"to"`
	Token     string `json:"token,omitempty"`
	UserID    int64  `json:"user_id"`
	CreatedAt int64  `json:"created_at"`
}

const (
	EmailQueueStream = "queue:email"
	MaxRetries       = 3
	RetryDelay       = 30 * time.Second
)

type Producer struct {
	redis *redis.Client
}

func NewProducer(rdb *redis.Client) *Producer {
	return &Producer{redis: rdb}
}

func (p *Producer) PublishEmailEvent(ctx context.Context, event EmailEvent) error {
	event.CreatedAt = time.Now().Unix()

	data, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("marshal event: %w", err)
	}

	// XADD: dodaj u stream, * = auto ID
	id, err := p.redis.XAdd(ctx, &redis.XAddArgs{
		Stream: EmailQueueStream,
		MaxLen: 10000,   // Max 10k poruka u streamu (stare se brišu)
		Approx: true,    // Approximate trimming (performansnije od točnog)
		Values: map[string]interface{}{
			"payload": string(data),
			"type":    event.Type,
		},
	}).Result()

	if err != nil {
		return fmt.Errorf("xadd: %w", err)
	}

	_ = id // npr: "1705312800123-0"
	return nil
}
```

---

## Registration handler — koristi Producer

```go
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	// ... validacija, insert user u MySQL ...

	// Publish async event (ne blokira HTTP request)
	event := queue.EmailEvent{
		Type:   "verify",
		To:     req.Email,
		Token:  verificationToken,
		UserID: userID,
	}

	if err := h.producer.PublishEmailEvent(r.Context(), event); err != nil {
		// Log warning ali NE vraća grešku klijentu.
		// Korisnik je registrovan — email će biti retryan od workera.
		h.logger.Warn("failed to queue email",
			zap.Error(err),
			zap.String("email", req.Email),
		)
	}

	respondJSON(w, http.StatusCreated, map[string]string{
		"message": "Registration successful. Check your email.",
	})
}
```

---

## Consumer — Go worker

```go
package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/user/project/internal/queue"
)

const (
	ConsumerGroup = "email-workers"
	BlockTimeout  = 5 * time.Second
)

type EmailWorker struct {
	redis  *redis.Client
	email  EmailService
	logger *zap.Logger
}

func NewEmailWorker(rdb *redis.Client, email EmailService, logger *zap.Logger) *EmailWorker {
	return &EmailWorker{redis: rdb, email: email, logger: logger}
}

func (w *EmailWorker) Start(ctx context.Context) error {
	// Kreiraj consumer group (idempotentno — ne faila ako već postoji)
	err := w.redis.XGroupCreateMkStream(ctx, queue.EmailQueueStream, ConsumerGroup, "0").Err()
	if err != nil && err.Error() != "BUSYGROUP Consumer Group name already exists" {
		return fmt.Errorf("create consumer group: %w", err)
	}

	// Unique consumer name po podu — sprječava koliziju u consumer groupu
	consumerName := fmt.Sprintf("worker-%s", os.Getenv("POD_NAME"))

	w.logger.Info("Email worker started", zap.String("consumer", consumerName))

	for {
		select {
		case <-ctx.Done():
			return nil
		default:
			if err := w.processMessages(ctx, consumerName); err != nil {
				w.logger.Error("process messages error", zap.Error(err))
				time.Sleep(5 * time.Second)
			}
		}
	}
}

func (w *EmailWorker) processMessages(ctx context.Context, consumerName string) error {
	// Prvo provjeri PEL (Pending Entries List) — poruke bez ACK-a
	pending, err := w.redis.XPending(ctx, queue.EmailQueueStream, ConsumerGroup).Result()
	if err == nil && pending.Count > 0 {
		w.reclaimOldMessages(ctx, consumerName)
	}

	// Čitaj nove poruke (block 5s ako nema ništa novo)
	streams, err := w.redis.XReadGroup(ctx, &redis.XReadGroupArgs{
		Group:    ConsumerGroup,
		Consumer: consumerName,
		Streams:  []string{queue.EmailQueueStream, ">"},  // ">" = samo unread poruke
		Count:    10,
		Block:    BlockTimeout,
	}).Result()

	if err == redis.Nil {
		return nil // Timeout — nema novih poruka, normalno stanje
	}
	if err != nil {
		return fmt.Errorf("xreadgroup: %w", err)
	}

	for _, stream := range streams {
		for _, msg := range stream.Messages {
			if err := w.processMessage(ctx, msg); err != nil {
				w.logger.Error("failed to process message",
					zap.String("id", msg.ID),
					zap.Error(err),
				)
				// Ne blokiramo petlju — loše poruke idu u reclaim/dead letter
			}
		}
	}
	return nil
}

func (w *EmailWorker) processMessage(ctx context.Context, msg redis.XMessage) error {
	payloadStr, ok := msg.Values["payload"].(string)
	if !ok {
		// Neispravan format — ACK i preskoči da ne blokira queue
		_ = w.redis.XAck(ctx, queue.EmailQueueStream, ConsumerGroup, msg.ID).Err()
		w.logger.Warn("invalid message payload, skipping", zap.String("id", msg.ID))
		return nil
	}

	var event queue.EmailEvent
	if err := json.Unmarshal([]byte(payloadStr), &event); err != nil {
		_ = w.redis.XAck(ctx, queue.EmailQueueStream, ConsumerGroup, msg.ID).Err()
		w.logger.Warn("unmarshal failed, skipping", zap.String("id", msg.ID), zap.Error(err))
		return nil
	}

	// Pokušaj poslati email
	if err := w.sendEmail(ctx, event); err != nil {
		w.handleRetry(ctx, msg, event, err)
		return err
	}

	// Uspjeh — ACK poruku
	return w.redis.XAck(ctx, queue.EmailQueueStream, ConsumerGroup, msg.ID).Err()
}

func (w *EmailWorker) handleRetry(ctx context.Context, msg redis.XMessage, event queue.EmailEvent, sendErr error) {
	retryCount := w.getRetryCount(ctx, msg.ID)

	if retryCount >= queue.MaxRetries {
		w.logger.Error("max retries reached, moving to dead letter",
			zap.String("id", msg.ID),
			zap.String("to", event.To),
			zap.Int("retries", retryCount),
		)
		// Premjesti u dead letter stream za ručnu inspekciju
		_ = w.redis.XAdd(ctx, &redis.XAddArgs{
			Stream: queue.EmailQueueStream + ":dead",
			Values: msg.Values,
		}).Err()
		_ = w.redis.XAck(ctx, queue.EmailQueueStream, ConsumerGroup, msg.ID).Err()
		return
	}

	// Inkrementiraj retry counter s TTL-om (čisti se automatski)
	retryKey := fmt.Sprintf("retry:%s", msg.ID)
	w.redis.Incr(ctx, retryKey)
	w.redis.Expire(ctx, retryKey, 1*time.Hour)

	w.logger.Warn("email send failed, will retry via PEL reclaim",
		zap.Int("attempt", retryCount+1),
		zap.Int("max_retries", queue.MaxRetries),
		zap.String("id", msg.ID),
		zap.Error(sendErr),
	)
	// Poruka ostaje u PEL — reclaimOldMessages je preuzima nakon min-idle-time
}

func (w *EmailWorker) getRetryCount(ctx context.Context, msgID string) int {
	val, err := w.redis.Get(ctx, fmt.Sprintf("retry:%s", msgID)).Int()
	if err != nil {
		return 0
	}
	return val
}

func (w *EmailWorker) reclaimOldMessages(ctx context.Context, consumerName string) {
	// Preuzmi poruke koje čekaju > 30s (vjerojatno od crashnutog workera)
	_, err := w.redis.XAutoClaim(ctx, &redis.XAutoClaimArgs{
		Stream:   queue.EmailQueueStream,
		Group:    ConsumerGroup,
		Consumer: consumerName,
		MinIdle:  30 * time.Second,
		Start:    "0-0",
		Count:    100,
	}).Result()
	if err != nil {
		w.logger.Warn("xautoclaim failed", zap.Error(err))
	}
}
```

---

## Main entrypoint — switch na worker mod

```go
// cmd/main.go
package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"

	"go.uber.org/zap"

	"github.com/user/project/internal/worker"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "worker" {
		runWorker()
		return
	}
	runAPIServer()
}

func runWorker() {
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	// Inicijaliziraj Redis, Email service iz env varijabli
	rdb := initRedis()
	emailSvc := initEmailService()

	w := worker.NewEmailWorker(rdb, emailSvc, logger)

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer cancel()

	logger.Info("Starting email worker")

	if err := w.Start(ctx); err != nil {
		logger.Fatal("worker error", zap.Error(err))
	}

	logger.Info("Email worker stopped gracefully")
}
```

---

## EmailService interface

```go
// internal/worker/email_service.go
package worker

import "context"

// EmailService je interface koji omogućava mockanje u testovima.
type EmailService interface {
	SendVerification(ctx context.Context, to, token string) error
	SendPasswordReset(ctx context.Context, to, token string) error
	SendWelcome(ctx context.Context, to string) error
}

func (w *EmailWorker) sendEmail(ctx context.Context, event queue.EmailEvent) error {
	switch event.Type {
	case "verify":
		return w.email.SendVerification(ctx, event.To, event.Token)
	case "reset_password":
		return w.email.SendPasswordReset(ctx, event.To, event.Token)
	case "welcome":
		return w.email.SendWelcome(ctx, event.To)
	default:
		w.logger.Warn("unknown email type, skipping", zap.String("type", event.Type))
		return nil
	}
}
```
