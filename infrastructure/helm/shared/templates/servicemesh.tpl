{{- if .Values.serviceMesh.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: istio-system
  labels:
    app.kubernetes.io/name: istio
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
  labels:
    app.kubernetes.io/name: istio
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
spec:
  mtls:
    mode: {{ if .Values.serviceMesh.mtls }}STRICT{{ else }}PERMISSIVE{{ end }}
{{- end }}
