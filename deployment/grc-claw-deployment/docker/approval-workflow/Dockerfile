# Approval Workflow — Temporal-based
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/approval-workflow ./cmd/workflow

FROM gcr.io/distroless/static-debian12 AS runtime
COPY --from=builder /out/approval-workflow /approval-workflow
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD ["/approval-workflow", "-health-check"]
ENTRYPOINT ["/approval-workflow"]
