{{- if .Values.cache.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: cache
  labels:
    app.kubernetes.io/name: cache
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: cache
  labels:
    app.kubernetes.io/name: redis
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
data:
  redis.conf: |
    maxmemory {{ .Values.cache.config.maxmemory }}
    maxmemory-policy {{ .Values.cache.config.maxmemory-policy }}
    appendonly yes
    save 900 1
    save 300 10
    save 60 10000
{{- end }}
