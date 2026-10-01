# Approval Workflow (Temporal) - Multi-stage build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o approval-workflow ./cmd/workflow

FROM gcr.io/distroless/static-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="approval-workflow" \
      grc.tier="control-plane"
COPY --from=builder /build/approval-workflow /approval-workflow
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/approval-workflow", "-health-check"]
ENTRYPOINT ["/approval-workflow"]
