{{/*
Expand the name of the chart.
*/}}
{{- define "auth-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "auth-app.fullname" -}}
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
Create chart label.
*/}}
{{- define "auth-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "auth-app.labels" -}}
helm.sh/chart: {{ include "auth-app.chart" . }}
{{ include "auth-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "auth-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "auth-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Redis fully qualified name.
*/}}
{{- define "auth-app.redis.fullname" -}}
{{- printf "%s-redis" (include "auth-app.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Redis URL built from the internal service name.
*/}}
{{- define "auth-app.redisUrl" -}}
{{- printf "redis://%s:%d/0" (include "auth-app.redis.fullname" .) (.Values.redis.service.port | int) }}
{{- end }}

{{/*
Name of the Secret that holds sensitive env vars.
*/}}
{{- define "auth-app.secretName" -}}
{{- if .Values.secrets.existingSecret }}
{{- .Values.secrets.existingSecret }}
{{- else }}
{{- include "auth-app.fullname" . }}
{{- end }}
{{- end }}

{{/*
Service account name.
*/}}
{{- define "auth-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "auth-app.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
