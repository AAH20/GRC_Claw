# PDP Service (OPA/Cedar) - Multi-stage build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o pdp-service ./cmd/pdp

FROM gcr.io/distroless/static-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="pdp-service" \
      grc.tier="control-plane"
COPY --from=builder /build/pdp-service /pdp-service
COPY --chown=nonroot:nonroot policies/ /policies/
USER 65534:65534
EXPOSE 8080 9090
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/pdp-service", "-health-check"]
ENTRYPOINT ["/pdp-service"]
