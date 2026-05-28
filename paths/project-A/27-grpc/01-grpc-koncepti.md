# 01 — gRPC Koncepti

## gRPC vs REST — kada koji

| Kriterij | REST/HTTP | gRPC |
|----------|-----------|------|
| Protokol | HTTP/1.1 ili 2 | HTTP/2 (obavezno) |
| Format | JSON (text) | Protocol Buffers (binary) |
| Kod gen | Ručno (OpenAPI) | Automatski iz .proto |
| Streaming | Ograničeno (SSE) | Bidirekcijalni streaming |
| Browser | Da | Ne direktno (grpc-web) |
| Debugging | curl, Postman | grpcurl, Postman (gRPC) |
| Performance | Dobro | 3-10x brže za serijalizaciju |
| Typed contract | OpenAPI spec | .proto fajl |
| Kada koristiti | Public API, browser, cross-language | Backend-to-backend, high throughput |

## 4 tipa gRPC komunikacije

```
Unary:            Klijent šalje jedan zahtjev, dobija jedan odgovor
                  (naš slučaj: SendEmail)

Server streaming: Klijent šalje jedan zahtjev, server šalje stream
                  (npr: live log streaming)

Client streaming: Klijent šalje stream, server odgovara jednom
                  (npr: bulk file upload)

Bidi streaming:   Oba šalju stream istovremeno
                  (npr: real-time chat)
```

**Za project-a:** Koristimo Unary pozive (pošalji notifikaciju → potvrdi primanje).

## Protobuf vs JSON

```protobuf
// Protobuf (binarno, ~30 bajtova):
message SendEmailRequest {
  string to    = 1;
  string token = 2;
  string type  = 3;
}

// JSON ekvivalent (~60 bajtova):
{"to":"user@firma.com","token":"abc123","type":"verify"}
```

Prednosti Protobuf-a:
- 2x manji payload
- 3-10x brža serijalizacija/deserijalizacija
- Strogo tipiziran ugovor između servisa
- Automatski generisan kod za sve podržane jezike (Go, Java, Python, C++...)

## Arhitektura u project-a

```
PHP service → HTTP/JSON → go-service (business logic)
                              │
                              └── gRPC → go-notification-service
                                           ├── send email (via Mailpit/SES)
                                           ├── async push notifications
                                           └── SMS (future)
```

PHP ostaje na HTTP/JSON jer je PHP gRPC klijent kompleksan za setup i održavanje.
gRPC se koristi isključivo za Go-to-Go komunikaciju gdje je typed kontrakt i
performansa kritična.

## Zašto ovako (ne direktno iz go-service)

- **Single responsibility:** go-service se bavi poslovnom logikom, ne email infrastrukturom
- **Skalabilnost:** notification-service skalira nezavisno od go-service
- **Dodavanje kanala:** SMS, push notifikacije — samo proširuješ .proto, ne diračeš go-service
- **Retry logika:** notification-service zna o email provajderima, go-service ne treba to znati
- **gRPC typed kontrakt:** kompajler hvata greške, ne runtime
