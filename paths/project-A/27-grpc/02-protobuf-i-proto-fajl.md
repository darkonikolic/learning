# 02 — Protobuf i .proto fajl

## Instalacija protoc kroz Docker (ne lokalno)

Ne instaliraš protoc lokalno — koristiš Docker da izbjegneš dependency hell
između verzija `protoc`, `protoc-gen-go`, i `protoc-gen-go-grpc`.

```bash
# Generiši Go kod iz .proto
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  ghcr.io/grpc-ecosystem/grpc-gateway/build:latest \
  protoc \
    --go_out=. \
    --go-grpc_out=. \
    proto/notification.proto
```

## notification.proto

```protobuf
syntax = "proto3";

package notification.v1;

option go_package = "github.com/youruser/project-a/gen/notification/v1;notificationv1";

// Notification service - svi tipovi notifikacija
service NotificationService {
  // Slanje email verifikacije
  rpc SendVerificationEmail(SendVerificationEmailRequest) returns (SendEmailResponse);

  // Slanje reset lozinke
  rpc SendPasswordResetEmail(SendPasswordResetEmailRequest) returns (SendEmailResponse);

  // Bulk status check (server streaming)
  rpc StreamDeliveryStatus(StreamDeliveryStatusRequest) returns (stream DeliveryStatus);
}

// ── Requests ──────────────────────────────────────────────
message SendVerificationEmailRequest {
  string to        = 1;   // email adresa
  string token     = 2;   // verifikacijski token
  string base_url  = 3;   // https://app.dev.firma.com
  int64  user_id   = 4;   // za logging i idempotency
}

message SendPasswordResetEmailRequest {
  string to        = 1;
  string token     = 2;
  string base_url  = 3;
  int64  user_id   = 4;
}

message StreamDeliveryStatusRequest {
  repeated string message_ids = 1;
}

// ── Responses ─────────────────────────────────────────────
message SendEmailResponse {
  bool   success    = 1;
  string message_id = 2;   // Za tracking
  string error      = 3;   // Prazan ako je uspjeh
}

message DeliveryStatus {
  string message_id = 1;
  string status     = 2;   // "sent", "delivered", "failed"
  int64  timestamp  = 3;
}
```

## Struktura direktorija

```
services/
├── go-service/
│   ├── proto/
│   │   └── notification.proto
│   └── gen/
│       └── notification/v1/
│           ├── notification.pb.go       ← auto-generated (poruke)
│           └── notification_grpc.pb.go  ← auto-generated (servis interface)
└── go-notification-service/
    ├── main.go
    ├── server/
    │   └── notification_server.go
    └── Dockerfile
```

`gen/` direktorij se commituje u git — nikada ne runiraš codegen na CI/CD.
Promjena .proto fajla = pokretanje `make proto` lokalno + commit promjena.

## Makefile target za codegen

```makefile
.PHONY: proto
proto:
	docker run --rm \
	  -v $(shell pwd):/workspace -w /workspace \
	  ghcr.io/grpc-ecosystem/grpc-gateway/build:latest \
	  protoc --go_out=. --go-grpc_out=. \
	  services/go-service/proto/notification.proto
```

## Proto konvencije

**Numerisanje polja:** Nikada ne mijenjaj postojeće brojeve polja (1, 2, 3...).
Dodaješ nova polja na kraj. Ako trebaš ukloniti polje, markiraj ga `reserved`.

```protobuf
message SendVerificationEmailRequest {
  reserved 5, 6;           // stara polja koja si uklonio
  reserved "old_field";    // za ime
  string to        = 1;
  string token     = 2;
  string base_url  = 3;
  int64  user_id   = 4;
  // novo polje na kraju:
  string locale    = 7;
}
```

**Versioning:** Paket je `notification.v1` — kada praveš breaking change, kreiraš
`notification.v2` i migruješ klijente postepeno. v1 ostaje dostupan dok ga
svi klijenti ne napuste.

**go_package format:** `"importpath;packagename"` — importpath je gdje će biti
fajl, packagename je Go paket name koji će se koristiti u kodu.
