# 04 — gRPC Klijent (Go)

## go-service: notification/client.go

```go
package notification

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/status"

	notificationv1 "github.com/youruser/project-a/gen/notification/v1"
)

// Client je thread-safe gRPC klijent za notification service.
// Jedna instanca po aplikaciji — dijeli se kao dependency.
type Client struct {
	conn   *grpc.ClientConn
	client notificationv1.NotificationServiceClient
	once   sync.Once
	logger *zap.Logger
}

func NewClient(target string, logger *zap.Logger) (*Client, error) {
	conn, err := grpc.Dial(
		target,
		// insecure.NewCredentials() je OK unutar K8s clustera.
		// Za TLS: grpc.WithTransportCredentials(credentials.NewTLS(tlsConfig))
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second, // ping interval ako nema aktivnosti
			Timeout:             5 * time.Second,  // čekanje na pong
			PermitWithoutStream: true,             // ping čak i bez aktivnih stream-ova
		}),
		// Round-robin za više instanci notification-service-a
		grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`),
	)
	if err != nil {
		return nil, fmt.Errorf("grpc dial %s: %w", target, err)
	}

	return &Client{
		conn:   conn,
		client: notificationv1.NewNotificationServiceClient(conn),
		logger: logger,
	}, nil
}

// SendVerificationEmail šalje zahtjev notification servisu.
// Vraća nil ako je email uspješno predat servisu (ne nužno dostavljen).
func (c *Client) SendVerificationEmail(
	ctx context.Context,
	to, token, baseURL string,
	userID int64,
) error {
	reqCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	resp, err := c.client.SendVerificationEmail(reqCtx, &notificationv1.SendVerificationEmailRequest{
		To:      to,
		Token:   token,
		BaseUrl: baseURL,
		UserId:  userID,
	})
	if err != nil {
		// Konvertuj gRPC status greške u smislene poruke
		if s, ok := status.FromError(err); ok {
			switch s.Code() {
			case codes.Unavailable:
				return fmt.Errorf("notification service unavailable: %w", err)
			case codes.DeadlineExceeded:
				return fmt.Errorf("notification service timeout: %w", err)
			case codes.InvalidArgument:
				return fmt.Errorf("invalid request: %s", s.Message())
			}
		}
		return fmt.Errorf("send verification email: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("notification service error: %s", resp.Error)
	}

	c.logger.Debug("verification email queued",
		zap.String("to", to),
		zap.Int64("user_id", userID),
		zap.String("message_id", resp.MessageId),
	)

	return nil
}

func (c *Client) SendPasswordResetEmail(
	ctx context.Context,
	to, token, baseURL string,
	userID int64,
) error {
	reqCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	resp, err := c.client.SendPasswordResetEmail(reqCtx, &notificationv1.SendPasswordResetEmailRequest{
		To:      to,
		Token:   token,
		BaseUrl: baseURL,
		UserId:  userID,
	})
	if err != nil {
		return fmt.Errorf("send password reset email: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("notification service error: %s", resp.Error)
	}

	return nil
}

// Close zatvara konekciju. Pozovi u defer u main.go.
func (c *Client) Close() error {
	return c.conn.Close()
}
```

## Inicijalizacija u go-service main.go

```go
notificationClient, err := notification.NewClient(
	os.Getenv("NOTIFICATION_SERVICE_ADDR"), // go-notification-service:50051
	logger,
)
if err != nil {
	logger.Fatal("failed to connect to notification service", zap.Error(err))
}
defer notificationClient.Close()

// Proslijedi klijentu kroz dependency injection
h := handlers.NewAuthHandler(db, notificationClient, cfg)
```

## Korišćenje u registration handleru

```go
// handlers/auth.go

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	// ... validacija i kreiranje usera ...

	token, err := h.repo.CreateVerificationToken(r.Context(), userID)
	if err != nil {
		// kritična greška — user nije kreiran bez tokena
		h.respondError(w, http.StatusInternalServerError, "registration failed")
		return
	}

	// Pošalji verifikacijski email — graceful degradation ako servis nije dostupan.
	// User je kreiran i može se prijaviti, email može kasniti.
	if err := h.notification.SendVerificationEmail(
		r.Context(),
		req.Email,
		token,
		h.config.BaseURL,
		userID,
	); err != nil {
		// Warn, ne Fatal — registracija je uspjela
		h.logger.Warn("verification email not sent",
			zap.String("email", req.Email),
			zap.Int64("user_id", userID),
			zap.Error(err),
		)
		// Možeš dodati zadatak u Redis Streams za retry
	}

	h.respondJSON(w, http.StatusCreated, map[string]any{
		"message": "Registration successful. Check your email for verification.",
		"user_id": userID,
	})
}
```

## grpcurl za debugging

```bash
# Instaliraj grpcurl (ili koristi Docker)
brew install grpcurl
# ili: docker run --rm fullstorydev/grpcurl ...

# Lista svih dostupnih servisa (zahtijeva reflection.Register u serveru)
grpcurl -plaintext go-notification-service:50051 list

# Lista metoda za konkretan servis
grpcurl -plaintext go-notification-service:50051 list notification.v1.NotificationService

# Pozovi SendVerificationEmail
grpcurl -plaintext \
  -d '{"to":"test@firma.com","token":"abc123","base_url":"http://localhost","user_id":1}' \
  go-notification-service:50051 \
  notification.v1.NotificationService/SendVerificationEmail

# Health check
grpcurl -plaintext go-notification-service:50051 grpc.health.v1.Health/Check

# Iz K8s poda:
kubectl exec -it deploy/go-service -n project-a-prod -- \
  grpcurl -plaintext go-notification-service:50051 list
```

## Retry pattern (opcionalno — za produkciju)

```go
// Za kritične notifikacije možeš dodati retry s exponential backoff.
// go-service ne brine o retry-ju za email — to je odgovornost notification-service-a.
// Ovdje je retry samo za mrežne greške (Unavailable, DeadlineExceeded).

import "google.golang.org/grpc/serviceconfig"

// Retry policy kroz service config (gRPC native retry):
grpc.WithDefaultServiceConfig(`{
  "loadBalancingPolicy": "round_robin",
  "methodConfig": [{
    "name": [{"service": "notification.v1.NotificationService"}],
    "retryPolicy": {
      "maxAttempts": 3,
      "initialBackoff": "0.5s",
      "maxBackoff": "5s",
      "backoffMultiplier": 2,
      "retryableStatusCodes": ["UNAVAILABLE", "DEADLINE_EXCEEDED"]
    }
  }]
}`)
```
