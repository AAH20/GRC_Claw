{{/*
Expand the name of the chart.
*/}}
{{- define "recruitment-platforms.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "recruitment-platforms.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "recruitment-platforms.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "recruitment-platforms.labels" -}}
helm.sh/chart: {{ include "recruitment-platforms.chart" . }}
{{ include "recruitment-platforms.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: recruitment-platforms
{{- end }}

{{/*
Selector labels
*/}}
{{- define "recruitment-platforms.selectorLabels" -}}
app.kubernetes.io/name: {{ include "recruitment-platforms.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "recruitment-platforms.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "recruitment-platforms.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Merge project config with defaults
*/}}
{{- define "recruitment-platforms.mergeConfig" -}}
{{- $defaults := .defaults }}
{{- $project := .project }}
{{- $merged := merge $defaults $project }}
{{- $merged | toYaml }}
{{- end }}

{{/*
Get project image
*/}}
{{- define "recruitment-platforms.image" -}}
{{- $global := .Values.global }}
{{- $project := .project }}
{{- $registry := $global.imageRegistry }}
{{- $repository := $project.image.repository | default .Values.defaults.image.repository }}
{{- $tag := $project.image.tag | default .Values.defaults.image.tag }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}

{{/*
Get project ingress hosts
*/}}
{{- define "recruitment-platforms.ingressHosts" -}}
{{- $global := .Values.global }}
{{- $project := .project }}
{{- if $project.ingress.hosts }}
{{- range $project.ingress.hosts }}
{{- . }}
{{- end }}
{{- else }}
{{- printf "%s.%s" $project.name $global.domain }}
{{- end }}
{{- end }}
