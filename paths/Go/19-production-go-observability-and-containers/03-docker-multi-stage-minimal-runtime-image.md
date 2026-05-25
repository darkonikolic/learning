# Unit 3 — Docker Multi-Stage: Minimal Runtime Image

## Concept

A multi-stage build uses two FROM statements in one Dockerfile. Stage 1 (builder) has the full Go toolchain and compiles the binary. Stage 2 (runtime) copies only the compiled binary into a minimal base image. The final image contains no Go compiler, no source code, no build tools, and no package manager — just the binary. This reduces image size from ~1 GB to ~10 MB and shrinks the attack surface dramatically. Set `CGO_ENABLED=0` to produce a statically linked binary that runs on `scratch` with no C library.

## Code

```dockerfile
# Stage 1: builder — full Go toolchain, produces static binary
FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0  → static binary (no libc dependency)
# -ldflags "-s -w" → strip debug symbols (smaller binary)
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w" \
    -o server \
    ./cmd/server

# Stage 2: runtime — no compiler, no source, no shell
FROM scratch

# Copy TLS root certificates so HTTPS calls work
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the binary from the builder stage
COPY --from=builder /app/server /server

# Non-root: scratch has no users, so set numeric UID
USER 65534:65534

EXPOSE 8080

ENTRYPOINT ["/server"]

# Image size comparison after this change:
#   Single-stage golang:1.23       ~1.1 GB
#   Multi-stage with alpine base   ~20  MB
#   Multi-stage with scratch base  ~8   MB
```

## Exercise

**Build:** Convert your API service Dockerfile to a multi-stage build using `scratch` as the final base.
**Input:** Your API service source code.
**Output:** A built image. Run `docker images` to see the size.
**Acceptance:** The scratch image must be under 20 MB. Run `docker run --rm <image>` and verify the server starts. Confirm `docker exec` into the container fails (no shell in scratch).

## Interview

- Why does `CGO_ENABLED=0` matter when using `scratch` as a base?
- What is the security advantage of having no shell in the runtime image?
- What do you lose by using `scratch` instead of `distroless`? When would you choose `distroless`?
