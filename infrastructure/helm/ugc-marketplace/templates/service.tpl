{{- range $project := .Values.projects }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: ugc
    app.kubernetes.io/part-of: ugc-marketplace
spec:
  type: {{ $project.service.type | default $.Values.defaults.service.type }}
  ports:
    - port: {{ $project.service.port | default $.Values.defaults.service.port }}
      targetPort: {{ $project.service.targetPort | default $.Values.defaults.service.targetPort }}
      protocol: {{ $project.service.protocol | default $.Values.defaults.service.protocol }}
      name: http
    - port: 9090
      targetPort: 9090
      protocol: TCP
      name: metrics
  selector:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
{{- end }}
