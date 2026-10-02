{{- if .Values.objectStorage.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: storage
  labels:
    app.kubernetes.io/name: storage
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: storage
  labels:
    app.kubernetes.io/name: minio
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
type: Opaque
data:
  MINIO_ACCESS_KEY: {{ .Values.secrets.MINIO_ACCESS_KEY | default "minioadmin" | b64enc | quote }}
  MINIO_SECRET_KEY: {{ .Values.secrets.MINIO_SECRET_KEY | default "minioadmin" | b64enc | quote }}
{{- end }}
