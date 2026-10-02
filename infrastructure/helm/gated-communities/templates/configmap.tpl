{{- range $project := .Values.projects }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}-config
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: communities
    app.kubernetes.io/part-of: gated-communities
data:
  {{- $config := merge $.Values.defaults.config $project.config }}
  {{- range $key, $value := $config }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
