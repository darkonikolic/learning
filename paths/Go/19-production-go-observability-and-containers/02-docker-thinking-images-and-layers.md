# Unit 2 — Docker: Images and Layers

## Concept

A Docker image is a stack of read-only layers. Each `RUN`, `COPY`, and `ADD` instruction creates a new layer on top of the previous one. Docker caches layers — if a layer's instruction and inputs have not changed since the last build, Docker reuses the cached layer and skips re-executing it. This means layer order determines build speed. Put slow, rarely-changing instructions first (installing dependencies) and fast, frequently-changing instructions last (copying your source code). A smaller base image reduces the attack surface and download time.

## Code

```dockerfile
# BAD ORDER — copies code first, so every code change
# invalidates the go mod download layer (slow network step).

FROM golang:1.23
WORKDIR /app
COPY . .                          # layer 1: everything — changes every commit
RUN go mod download               # layer 2: re-runs on every code change
RUN go build -o server .          # layer 3: rebuild

# ---

# GOOD ORDER — dependency layer is cached until go.mod changes.

FROM golang:1.23
WORKDIR /app
COPY go.mod go.sum ./             # layer 1: only changes when deps change
RUN go mod download               # layer 2: cached until go.mod changes
COPY . .                          # layer 3: source code — changes often
RUN go build -o server .          # layer 4: rebuild only when code changes

# Base image size comparison (approximate):
#   ubuntu:22.04     ~77 MB
#   debian:bookworm-slim  ~74 MB
#   golang:1.23-alpine    ~250 MB (includes Go toolchain)
#   alpine:3.19      ~7 MB
#   scratch          0 MB (empty — just your binary)
#   gcr.io/distroless/static  ~2 MB (libc, certs, no shell)
```

## Exercise

**Build:** Package your API service as a Docker image using the good-order Dockerfile above.
**Input:** Your API service source code with `go.mod` and `go.sum`.
**Output:** A built Docker image. Run `docker history <image>` to see the layer breakdown.
**Acceptance:** Make a trivial code change (add a comment), rebuild, and confirm only the last two layers are rebuilt (COPY and build). Then swap the COPY and `go mod download` order and rebuild — confirm all layers invalidate.

## Interview

- Why does Docker layer order affect build time in CI?
- What is the practical difference between `alpine` and `scratch` as a base image?
- If you add a secret to a `RUN` layer and then delete it in the next layer, is the secret safe?
