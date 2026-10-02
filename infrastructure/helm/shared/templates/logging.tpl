{{- if .Values.logging.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: logging
  labels:
    app.kubernetes.io/name: logging
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: logging
  labels:
    app.kubernetes.io/name: loki
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
data:
  loki.yaml: |
    auth_enabled: false
    server:
      http_listen_port: 3100
    common:
      instance_addr: 127.0.0.1
      path_prefix: /loki
      storage:
        filesystem:
          chunks_directory: /loki/chunks
          rules_directory: /loki/rules
      replication_factor: 1
      ring:
        kvstore:
          store: inmemory
    schema_config:
      configs:
        - from: 2020-10-24
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h
    limits_config:
      reject_old_samples: true
      reject_old_samples_max_age: 168h
{{- end }}
