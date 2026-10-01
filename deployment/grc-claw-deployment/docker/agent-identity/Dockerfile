# Agent Identity — SPIRE-based SVID issuance
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/agent-identity ./cmd/identity

FROM gcr.io/distroless/static-debian12 AS runtime
COPY --from=builder /out/agent-identity /agent-identity
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/agent-identity", "-health-check"]
ENTRYPOINT ["/agent-identity"]
