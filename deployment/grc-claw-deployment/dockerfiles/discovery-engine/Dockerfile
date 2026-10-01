# Discovery Engine (Scanners) - Multi-stage build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o discovery-engine ./cmd/discovery

FROM gcr.io/distroless/static-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="discovery-engine" \
      grc.tier="analytics"
COPY --from=builder /build/discovery-engine /discovery-engine
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/discovery-engine", "-health-check"]
ENTRYPOINT ["/discovery-engine"]
