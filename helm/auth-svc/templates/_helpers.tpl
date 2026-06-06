{{/*
Expand the name of the chart.
*/}}
{{- define "auth-svc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "auth-svc.fullname" -}}
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
{{- define "auth-svc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "auth-svc.labels" -}}
helm.sh/chart: {{ include "auth-svc.chart" . }}
{{ include "auth-svc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "auth-svc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "auth-svc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Redis fully qualified name.
*/}}
{{- define "auth-svc.redis.fullname" -}}
{{- printf "%s-redis" (include "auth-svc.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Redis URL built from the internal service name.
*/}}
{{- define "auth-svc.redisUrl" -}}
{{- printf "redis://%s:%d/0" (include "auth-svc.redis.fullname" .) (.Values.redis.service.port | int) }}
{{- end }}

{{/*
Name of the Secret that holds sensitive env vars.
*/}}
{{- define "auth-svc.secretName" -}}
{{- if .Values.secrets.existingSecret }}
{{- .Values.secrets.existingSecret }}
{{- else }}
{{- include "auth-svc.fullname" . }}
{{- end }}
{{- end }}

{{/*
Service account name.
*/}}
{{- define "auth-svc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "auth-svc.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
