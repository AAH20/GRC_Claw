{{/* Common labels */}}
{{- define "grc-claw.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: grc-claw
{{- end -}}

{{/* Selector labels */}}
{{- define "grc-claw.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Image */}}
{{- define "grc-claw.image" -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .repository .tag -}}
{{- end -}}
