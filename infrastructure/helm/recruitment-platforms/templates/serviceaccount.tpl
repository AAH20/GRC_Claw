{{- range $project := .Values.projects }}
{{- if ($project.serviceAccount | default $.Values.defaults.serviceAccount).create }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: recruitment
    app.kubernetes.io/part-of: recruitment-platforms
  {{- with ($project.serviceAccount | default $.Values.defaults.serviceAccount).annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
{{- end }}
