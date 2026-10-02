{{- if .Values.certManager.enabled }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: cert-manager
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/part-of: shared
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ahmed@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
{{- end }}
