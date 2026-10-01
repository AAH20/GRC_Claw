# PEP Gateway — MCP/Envoy enforcement proxy
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/pep-gateway ./cmd/pep

FROM gcr.io/distroless/static-debian12 AS runtime
COPY --from=builder /out/pep-gateway /pep-gateway
USER 65534:65534
EXPOSE 8080 9090
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/pep-gateway", "-health-check"]
ENTRYPOINT ["/pep-gateway"]
