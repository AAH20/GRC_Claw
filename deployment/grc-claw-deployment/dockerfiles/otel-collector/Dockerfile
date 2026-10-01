# OpenTelemetry Collector - Multi-stage build
FROM otel/opentelemetry-collector-contrib:0.91.0 AS base
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="otel-collector" \
      grc.tier="observability"
COPY --chown=nonroot:nonroot config.yaml /etc/otel-collector/config.yaml
USER 65534:65534
EXPOSE 4317 4318 8888
ENTRYPOINT ["/otelcol-contrib"]
CMD ["--config=/etc/otel-collector/config.yaml"]
