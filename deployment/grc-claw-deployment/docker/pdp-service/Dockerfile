# PDP Service — OPA/Cedar policy evaluation
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/pdp-service ./cmd/pdp

FROM gcr.io/distroless/static-debian12 AS runtime
COPY --from=builder /out/pdp-service /pdp-service
COPY --chown=nonroot:nonroot policies/ /policies/
USER 65534:65534
EXPOSE 8080 9090
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/pdp-service", "-health-check"]
ENTRYPOINT ["/pdp-service"]
