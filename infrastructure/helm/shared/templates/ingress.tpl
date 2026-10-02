{{- if .Values.ingressController.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: {{ .Release.Name }}
data:
  use-forwarded-headers: "{{ .Values.ingressController.config.use-forwarded-headers }}"
  compute-full-forwarded-for: "{{ .Values.ingressController.config.compute-full-forwarded-for }}"
  use-proxy-protocol: "{{ .Values.ingressController.config.use-proxy-protocol }}"
{{- end }}
