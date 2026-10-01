# OpenTelemetry Collector
FROM otel/opentelemetry-collector-contrib:0.91.0 AS base
COPY --chown=nonroot:nonroot config.yaml /etc/otel-collector-config.yaml
USER 65534:65534
EXPOSE 4317 4318 8888
ENTRYPOINT ["/otelcol-contrib"]
CMD ["--config=/etc/otel-collector-config.yaml"]
