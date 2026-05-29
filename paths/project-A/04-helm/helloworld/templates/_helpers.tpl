{{/*
helloworld.fullname — generiše ime za sve resurse ovog chart-a.
Uključuje .Release.Name da bi više release-ova moglo da koegzistira u istom
namespace-u (npr. dva MR review okruženja) bez kolizije imena resursa.
*/}}
{{- define "helloworld.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
helloworld.labels — zajedničke labele koje idu na sve resurse.
*/}}
{{- define "helloworld.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
helloworld.selectorLabels — labele po kojima Deployment i Service "pronalaze" podove.
Moraju biti stabilne (ne menjaju se po verziji), zato su odvojene od helloworld.labels.
*/}}
{{- define "helloworld.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
