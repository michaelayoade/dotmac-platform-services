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
