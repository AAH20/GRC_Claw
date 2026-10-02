{{- range $project := .Values.projects }}
{{- $secrets := merge $.Values.defaults.secrets $project.secrets }}
{{- $hasSecrets := false }}
{{- range $key, $value := $secrets }}
{{- if $value }}
{{- $hasSecrets = true }}
{{- end }}
{{- end }}
{{- if $hasSecrets }}
---
apiVersion: v1
kind: Secret
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}-secret
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: communities
    app.kubernetes.io/part-of: gated-communities
type: Opaque
data:
  {{- range $key, $value := $secrets }}
  {{- if $value }}
  {{ $key }}: {{ $value | b64enc | quote }}
  {{- end }}
  {{- end }}
{{- end }}
{{- end }}
