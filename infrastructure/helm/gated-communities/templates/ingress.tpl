{{- range $project := .Values.projects }}
{{- if ($project.ingress | default $.Values.defaults.ingress).enabled }}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: communities
    app.kubernetes.io/part-of: gated-communities
  annotations:
    {{- with ($project.ingress | default $.Values.defaults.ingress).annotations }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  ingressClassName: {{ ($project.ingress | default $.Values.defaults.ingress).className }}
  {{- if ($project.ingress | default $.Values.defaults.ingress).tls }}
  {{- if ($project.ingress | default $.Values.defaults.ingress).tls.enabled }}
  tls:
    - hosts:
        {{- range ($project.ingress | default $.Values.defaults.ingress).hosts }}
        - {{ . }}
        {{- end }}
        {{- if $project.ingress.hosts }}
        {{- range $project.ingress.hosts }}
        - {{ . }}
        {{- end }}
        {{- end }}
      secretName: {{ ($project.ingress | default $.Values.defaults.ingress).tls.secretName }}
  {{- end }}
  {{- end }}
  rules:
    {{- $hosts := list }}
    {{- if $project.ingress.hosts }}
    {{- range $project.ingress.hosts }}
    {{- $hosts = append $hosts . }}
    {{- end }}
    {{- else }}
    {{- $hosts = append $hosts (printf "%s.%s" $project.name $.Values.global.domain) }}
    {{- end }}
    {{- range $hosts }}
    - host: {{ . }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ $.Release.Name }}-{{ $project.name }}
                port:
                  number: {{ $project.service.port | default $.Values.defaults.service.port }}
    {{- end }}
{{- end }}
{{- end }}
