{{- range $project := .Values.projects }}
{{- if ($project.podDisruptionBudget | default $.Values.defaults.podDisruptionBudget).enabled }}
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: communities
    app.kubernetes.io/part-of: gated-communities
spec:
  minAvailable: {{ ($project.podDisruptionBudget | default $.Values.defaults.podDisruptionBudget).minAvailable }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ $project.name }}
      app.kubernetes.io/instance: {{ $.Release.Name }}
{{- end }}
{{- end }}
