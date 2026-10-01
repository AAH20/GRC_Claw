# Agent Identity (SPIRE) - Multi-stage build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o agent-identity ./cmd/identity

FROM gcr.io/distroless/static-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="agent-identity" \
      grc.tier="control-plane"
COPY --from=builder /build/agent-identity /agent-identity
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/agent-identity", "-health-check"]
ENTRYPOINT ["/agent-identity"]
