{{- range $project := .Values.projects }}
{{- if ($project.autoscaling | default $.Values.defaults.autoscaling).enabled }}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: recruitment
    app.kubernetes.io/part-of: recruitment-platforms
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ $.Release.Name }}-{{ $project.name }}
  minReplicas: {{ ($project.autoscaling | default $.Values.defaults.autoscaling).minReplicas }}
  maxReplicas: {{ ($project.autoscaling | default $.Values.defaults.autoscaling).maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ ($project.autoscaling | default $.Values.defaults.autoscaling).targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ ($project.autoscaling | default $.Values.defaults.autoscaling).targetMemoryUtilizationPercentage }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
{{- end }}
{{- end }}
