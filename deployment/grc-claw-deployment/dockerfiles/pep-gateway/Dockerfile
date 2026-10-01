# PEP Gateway (MCP/Envoy) - Multi-stage build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o pep-gateway ./cmd/pep

FROM gcr.io/distroless/static-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="pep-gateway" \
      grc.tier="control-plane"
COPY --from=builder /build/pep-gateway /pep-gateway
USER 65534:65534
EXPOSE 8080 9090
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/pep-gateway", "-health-check"]
ENTRYPOINT ["/pep-gateway"]
