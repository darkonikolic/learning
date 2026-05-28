# 06 — gRPC u Projektu: Kada i Zašto

## Finalna arhitektura sa gRPC

```
Browser (Vue.js)
    │ HTTP/JSON
    ▼
nginx (reverse proxy)
    │ HTTP/JSON (FastCGI)
    ▼
php-service (API proxy/gateway)
    │ HTTP/JSON
    ▼
go-service (business logic)
    │ gRPC (binary, HTTP/2)
    ▼
go-notification-service
    ├── Email (Mailpit dev / SES prod)
    └── (budući: SMS via Twilio, Push via FCM)
```

## Kada dodati gRPC u projekt

| Situacija | Dodaj gRPC? |
|-----------|-------------|
| Imaš drugi Go servis koji treba pozivati | Da |
| Performanse između servisa su bottleneck | Da |
| Trebaš streaming (npr. real-time dashboard) | Da |
| Tim raste, potreban typed kontrakt između timova | Da |
| Jedini klijent je browser | Ne — REST |
| PHP treba direktno pozivati Go | Ne — HTTP/JSON |
| Projekt je mali mono-servis | Ne — overhead nije opravdan |

## Kada NE koristiti gRPC

**Browser:** Browseri ne podržavaju gRPC direktno. Trebaš grpc-web proxy
(Envoy) koji dodaje kompleksnost. Koristi REST + Fetch API.

**PHP klijent:** PHP gRPC library je kompleksna za setup, zahtijeva
`grpc` PHP extension koji se ne kompajlira svuda, i ima lošu Docker podršku.
Za PHP → Go komunikaciju, HTTP/JSON je prava odluka.

**Mono-servis:** Ako imaš jedan servis koji radi sve, gRPC overhead
(generisanje koda, versioning .proto-a, poseban port) nije opravdan.

## Alternativa: gRPC Gateway (REST + gRPC isti kod)

Ako trebaš i PHP (REST) i Go (gRPC) da pozivaju isti servis:

```
External clients (browser, PHP) → HTTP/JSON REST ─┐
                                                    ├→ grpc-gateway → gRPC servis
Internal Go services             → gRPC direktno ──┘
```

grpc-gateway auto-generira REST API iz .proto anotacija:

```protobuf
import "google/api/annotations.proto";

service NotificationService {
  rpc SendVerificationEmail(SendVerificationEmailRequest) returns (SendEmailResponse) {
    option (google.api.http) = {
      post: "/v1/notifications/verify-email"
      body: "*"
    };
  };
}
```

Iz ove anotacije dobijamo i gRPC i REST endpoint bez dupliranja logike.
Za project-a ovo nije potrebno jer PHP ne poziva notification servis direktno.

## Testiranje gRPC servisa

### Unit test servera (mock email sender)

```go
// server/notification_server_test.go
package server_test

import (
	"context"
	"testing"

	"go.uber.org/zap/zaptest"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	notificationv1 "github.com/youruser/project-a/gen/notification/v1"
	"github.com/youruser/project-a/services/go-notification-service/server"
)

type MockEmailSender struct {
	called  bool
	lastMsg server.EmailMessage
	err     error
}

func (m *MockEmailSender) Send(_ context.Context, msg server.EmailMessage) error {
	m.called = true
	m.lastMsg = msg
	return m.err
}

func TestSendVerificationEmail_Success(t *testing.T) {
	mock := &MockEmailSender{}
	srv := server.NewNotificationServerWithEmail(zaptest.NewLogger(t), mock)

	resp, err := srv.SendVerificationEmail(context.Background(), &notificationv1.SendVerificationEmailRequest{
		To:      "test@firma.com",
		Token:   "test-token-123",
		BaseUrl: "https://app.test",
		UserId:  42,
	})

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !resp.Success {
		t.Error("expected Success=true")
	}
	if resp.MessageId == "" {
		t.Error("expected non-empty MessageId")
	}
	if !mock.called {
		t.Error("expected email sender to be called")
	}
	if mock.lastMsg.To != "test@firma.com" {
		t.Errorf("expected To=test@firma.com, got %s", mock.lastMsg.To)
	}
}

func TestSendVerificationEmail_ValidationError(t *testing.T) {
	srv := server.NewNotificationServerWithEmail(zaptest.NewLogger(t), &MockEmailSender{})

	_, err := srv.SendVerificationEmail(context.Background(), &notificationv1.SendVerificationEmailRequest{
		To:    "",  // prazan To — treba da vrati InvalidArgument
		Token: "token",
	})

	if err == nil {
		t.Fatal("expected error, got nil")
	}
	s, _ := status.FromError(err)
	if s.Code() != codes.InvalidArgument {
		t.Errorf("expected InvalidArgument, got %v", s.Code())
	}
}

func TestSendVerificationEmail_EmailSenderError(t *testing.T) {
	mock := &MockEmailSender{err: fmt.Errorf("smtp connection refused")}
	srv := server.NewNotificationServerWithEmail(zaptest.NewLogger(t), mock)

	_, err := srv.SendVerificationEmail(context.Background(), &notificationv1.SendVerificationEmailRequest{
		To:      "test@firma.com",
		Token:   "token",
		BaseUrl: "https://app.test",
		UserId:  1,
	})

	if err == nil {
		t.Fatal("expected error")
	}
	s, _ := status.FromError(err)
	if s.Code() != codes.Internal {
		t.Errorf("expected Internal, got %v", s.Code())
	}
}
```

### Integracija test sa bufconn (bez pravog TCP-a)

```go
// Koristi google.golang.org/grpc/test/bufconn za in-process gRPC testiranje.
// Server i klijent komuniciraju kroz in-memory buffer — nema porta, nema race conditiona.

import "google.golang.org/grpc/test/bufconn"

const bufSize = 1024 * 1024

func setupTestServer(t *testing.T) (notificationv1.NotificationServiceClient, func()) {
	lis := bufconn.Listen(bufSize)
	srv := grpc.NewServer()
	notificationv1.RegisterNotificationServiceServer(
		srv,
		server.NewNotificationServerWithEmail(zaptest.NewLogger(t), &MockEmailSender{}),
	)
	go srv.Serve(lis)

	conn, _ := grpc.DialContext(context.Background(), "bufnet",
		grpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {
			return lis.DialContext(ctx)
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)

	cleanup := func() {
		conn.Close()
		srv.Stop()
		lis.Close()
	}

	return notificationv1.NewNotificationServiceClient(conn), cleanup
}
```

## Migracija iz goroutine pristupa na gRPC

Stari pristup (iz modula 26-async-i-queues):
```go
// go-service: direktno slanje emaila iz goroutine
go func() {
	if err := emailSender.SendVerificationEmail(req.Email, token); err != nil {
		logger.Error("email failed", zap.Error(err))
	}
}()
```

Novi pristup (gRPC notification service):
```go
// go-service: delegira notification servisu
if err := h.notification.SendVerificationEmail(
	r.Context(), req.Email, token, h.config.BaseURL, userID,
); err != nil {
	h.logger.Warn("notification unavailable", zap.Error(err))
}
```

Prednosti novog pristupa:
- **Observability:** notification-service loguje svaki pokušaj centralno
- **Retry:** notification-service upravlja retry logikom, go-service ne treba znati
- **Skalabilnost:** notification-service skalira nezavisno od go-service
- **Testabilnost:** mock `NotificationClient` interface u go-service testovima
- **Typed kontrakt:** kompajler hvata greške pri promjeni API-ja
