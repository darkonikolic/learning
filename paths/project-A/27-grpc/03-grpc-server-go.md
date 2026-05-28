# 03 — gRPC Server (Go)

## go-notification-service/main.go

```go
package main

import (
	"context"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"

	notificationv1 "github.com/youruser/project-a/gen/notification/v1"
	"github.com/youruser/project-a/services/go-notification-service/server"
)

func main() {
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	port := os.Getenv("GRPC_PORT")
	if port == "" {
		port = "50051"
	}

	lis, err := net.Listen("tcp", ":"+port)
	if err != nil {
		logger.Fatal("failed to listen", zap.Error(err))
	}

	// Interceptors (middleware za gRPC)
	grpcServer := grpc.NewServer(
		grpc.ChainUnaryInterceptor(
			loggingInterceptor(logger),
			recoveryInterceptor(),
		),
	)

	// Registruj servise
	notificationSrv := server.NewNotificationServer(logger)
	notificationv1.RegisterNotificationServiceServer(grpcServer, notificationSrv)

	// Health check (za K8s probes)
	grpc_health_v1.RegisterHealthServer(grpcServer, notificationSrv)

	// Reflection (za grpcurl debugging)
	reflection.Register(grpcServer)

	logger.Info("gRPC server listening", zap.String("port", port))

	// Graceful shutdown
	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM)
	defer cancel()

	go func() {
		<-ctx.Done()
		grpcServer.GracefulStop()
	}()

	if err := grpcServer.Serve(lis); err != nil {
		logger.Fatal("server failed", zap.Error(err))
	}
}

func loggingInterceptor(logger *zap.Logger) grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		start := time.Now()
		resp, err := handler(ctx, req)
		logger.Info("gRPC call",
			zap.String("method", info.FullMethod),
			zap.Duration("duration", time.Since(start)),
			zap.Error(err),
		)
		return resp, err
	}
}

func recoveryInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (resp interface{}, err error) {
		defer func() {
			if r := recover(); r != nil {
				err = status.Errorf(codes.Internal, "panic: %v", r)
			}
		}()
		return handler(ctx, req)
	}
}
```

## server/notification_server.go

```go
package server

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/smtp"
	"os"

	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/status"

	notificationv1 "github.com/youruser/project-a/gen/notification/v1"
)

// EmailMessage je interni model, nezavisan od proto poruka.
type EmailMessage struct {
	To      string
	Subject string
	Body    string
}

// EmailSender interface omogućava mock u testovima.
type EmailSender interface {
	Send(ctx context.Context, msg EmailMessage) error
}

// SMTPSender je produkcijska implementacija za Mailpit/SES.
type SMTPSender struct {
	host     string
	port     string
	from     string
	username string
	password string
}

func NewSMTPSender() *SMTPSender {
	return &SMTPSender{
		host:     os.Getenv("SMTP_HOST"),
		port:     os.Getenv("SMTP_PORT"),
		from:     os.Getenv("SMTP_FROM"),
		username: os.Getenv("SMTP_USERNAME"),
		password: os.Getenv("SMTP_PASSWORD"),
	}
}

func (s *SMTPSender) Send(_ context.Context, msg EmailMessage) error {
	auth := smtp.PlainAuth("", s.username, s.password, s.host)
	body := fmt.Sprintf(
		"To: %s\r\nFrom: %s\r\nSubject: %s\r\n\r\n%s",
		msg.To, s.from, msg.Subject, msg.Body,
	)
	return smtp.SendMail(
		s.host+":"+s.port,
		auth,
		s.from,
		[]string{msg.To},
		[]byte(body),
	)
}

// NotificationServer implementira proto interface i health check.
type NotificationServer struct {
	notificationv1.UnimplementedNotificationServiceServer
	grpc_health_v1.UnimplementedHealthServer
	logger *zap.Logger
	email  EmailSender
}

func NewNotificationServer(logger *zap.Logger) *NotificationServer {
	return &NotificationServer{
		logger: logger,
		email:  NewSMTPSender(),
	}
}

// NewNotificationServerWithEmail koristi se u testovima za injektovanje mocka.
func NewNotificationServerWithEmail(logger *zap.Logger, email EmailSender) *NotificationServer {
	return &NotificationServer{logger: logger, email: email}
}

func (s *NotificationServer) SendVerificationEmail(
	ctx context.Context,
	req *notificationv1.SendVerificationEmailRequest,
) (*notificationv1.SendEmailResponse, error) {

	if req.To == "" || req.Token == "" {
		return nil, status.Error(codes.InvalidArgument, "to and token are required")
	}

	verifyURL := fmt.Sprintf("%s/verify?token=%s", req.BaseUrl, req.Token)

	if err := s.email.Send(ctx, EmailMessage{
		To:      req.To,
		Subject: "Verify your email",
		Body:    fmt.Sprintf("Click to verify: %s", verifyURL),
	}); err != nil {
		s.logger.Error("failed to send verification email",
			zap.String("to", req.To),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "failed to send email")
	}

	msgID := generateMessageID()
	s.logger.Info("verification email sent",
		zap.String("to", req.To),
		zap.Int64("user_id", req.UserId),
		zap.String("message_id", msgID),
	)

	return &notificationv1.SendEmailResponse{
		Success:   true,
		MessageId: msgID,
	}, nil
}

func (s *NotificationServer) SendPasswordResetEmail(
	ctx context.Context,
	req *notificationv1.SendPasswordResetEmailRequest,
) (*notificationv1.SendEmailResponse, error) {

	if req.To == "" || req.Token == "" {
		return nil, status.Error(codes.InvalidArgument, "to and token are required")
	}

	resetURL := fmt.Sprintf("%s/reset-password?token=%s", req.BaseUrl, req.Token)

	if err := s.email.Send(ctx, EmailMessage{
		To:      req.To,
		Subject: "Reset your password",
		Body:    fmt.Sprintf("Click to reset your password: %s\n\nLink expires in 1 hour.", resetURL),
	}); err != nil {
		s.logger.Error("failed to send password reset email",
			zap.String("to", req.To),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "failed to send email")
	}

	msgID := generateMessageID()
	s.logger.Info("password reset email sent",
		zap.String("to", req.To),
		zap.Int64("user_id", req.UserId),
		zap.String("message_id", msgID),
	)

	return &notificationv1.SendEmailResponse{
		Success:   true,
		MessageId: msgID,
	}, nil
}

// StreamDeliveryStatus je primjer server streaming RPC-a.
// Klijent šalje listu message_id-eva, server vrača status za svaki.
func (s *NotificationServer) StreamDeliveryStatus(
	req *notificationv1.StreamDeliveryStatusRequest,
	stream notificationv1.NotificationService_StreamDeliveryStatusServer,
) error {
	for _, msgID := range req.MessageIds {
		// U produkciji: lookup iz baze/Redisa
		if err := stream.Send(&notificationv1.DeliveryStatus{
			MessageId: msgID,
			Status:    "delivered",
			Timestamp: time.Now().Unix(),
		}); err != nil {
			return status.Errorf(codes.Internal, "stream send failed: %v", err)
		}
	}
	return nil
}

// Check implementira gRPC health protocol — koristi K8s za readiness/liveness probe.
func (s *NotificationServer) Check(
	_ context.Context,
	req *grpc_health_v1.HealthCheckRequest,
) (*grpc_health_v1.HealthCheckResponse, error) {
	return &grpc_health_v1.HealthCheckResponse{
		Status: grpc_health_v1.HealthCheckResponse_SERVING,
	}, nil
}

func generateMessageID() string {
	b := make([]byte, 8)
	rand.Read(b)
	return hex.EncodeToString(b)
}
```

## go.mod za go-notification-service

```
module github.com/youruser/project-a/services/go-notification-service

go 1.22

require (
    go.uber.org/zap v1.27.0
    google.golang.org/grpc v1.64.0
    google.golang.org/protobuf v1.34.1
    github.com/youruser/project-a/gen v0.0.0
)

replace github.com/youruser/project-a/gen => ../../gen
```

## Dockerfile za go-notification-service

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# gen/ je shared — kopiraš ga u build kontekst
COPY ../../gen ./gen
RUN CGO_ENABLED=0 GOOS=linux go build -o notification-service ./main.go

FROM gcr.io/distroless/static-debian12
COPY --from=builder /build/notification-service /notification-service
EXPOSE 50051
ENTRYPOINT ["/notification-service"]
```
