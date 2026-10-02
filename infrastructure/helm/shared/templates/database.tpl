{{- if .Values.database.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: database
  labels:
    app.kubernetes.io/name: database
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgresql-config
  namespace: database
  labels:
    app.kubernetes.io/name: postgresql
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
data:
  POSTGRES_DB: grc_claw
  POSTGRES_USER: grc_claw
  maxConnections: "{{ .Values.database.config.maxConnections }}"
  sharedBuffers: "{{ .Values.database.config.sharedBuffers }}"
---
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-credentials
  namespace: database
  labels:
    app.kubernetes.io/name: postgresql
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
type: Opaque
data:
  POSTGRES_PASSWORD: {{ .Values.secrets.DB_PASSWORD | default "changeme" | b64enc | quote }}
{{- end }}
