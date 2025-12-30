{{- define "dotmac-platform.name" -}}
dotmac-platform
{{- end -}}

{{- define "dotmac-platform.fullname" -}}
{{ .Release.Name }}
{{- end -}}

{{- define "dotmac-platform.labels" -}}
app.kubernetes.io/name: {{ include "dotmac-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: Helm
{{- end -}}

{{- define "dotmac-platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (printf "%s-sa" (include "dotmac-platform.fullname" .)) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
