{{- range $project := .Values.projects }}
{{- if ($project.networkPolicy | default $.Values.defaults.networkPolicy).enabled }}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: ugc
    app.kubernetes.io/part-of: ugc-marketplace
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: {{ $project.name }}
      app.kubernetes.io/instance: {{ $.Release.Name }}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: {{ $.Release.Namespace }}
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: {{ $project.service.targetPort | default $.Values.defaults.service.targetPort }}
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: {{ $.Release.Namespace }}
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
{{- end }}
{{- end }}
