#!/usr/bin/env python3
"""
Helm Chart Generator for Kubernetes Deployments
Generates complete Helm chart structure with templates and values files.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List

def create_chart_yaml(app_name: str, version: str, api_version: str = "v2") -> str:
    """Generate Chart.yaml content."""
    return f"""apiVersion: {api_version}
name: {app_name}
description: A Helm chart for {app_name} Kubernetes deployment
type: application
version: {version}
appVersion: "1.0.0"
maintainers:
  - name: DevOps Team
    email: devops@example.com
keywords:
  - microservices
  - kubernetes
  - deployment
"""

def create_values_yaml(services: List[str], features: Dict[str, bool]) -> str:
    """Generate values.yaml content."""
    services_config = "\n".join([
        f"  {service.replace('-', '')}:\n"
        f"    enabled: true\n"
        f"    replicaCount: 2\n"
        f"    image:\n"
        f"      repository: {service}\n"
        f"      tag: latest\n"
        f"      pullPolicy: IfNotPresent\n"
        f"    resources:\n"
        f"      requests:\n"
        f"        cpu: 200m\n"
        f"        memory: 256Mi\n"
        f"      limits:\n"
        f"        cpu: 1000m\n"
        f"        memory: 1Gi"
        for service in services
    ])

    autoscaling = ""
    if features.get("autoscaling", False):
        autoscaling = """
autoscaling:
  enabled: true
  backend:
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 75
  frontend:
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
"""

    ingress = ""
    if features.get("ingress", False):
        tls_config = """
  tls:
    - secretName: app-tls
      hosts:
        - example.com""" if features.get("tls", False) else ""

        ingress = f"""
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: example.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: backend{tls_config}
"""

    dapr_config = ""
    if features.get("dapr", False):
        dapr_config = """
dapr:
  enabled: true
  logLevel: info
  appPort: 8000
"""

    monitoring = ""
    if features.get("monitoring", False):
        monitoring = """
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
"""

    return f"""global:
  environment: production
  domain: example.com
  registry: ghcr.io/username
  imagePullSecrets: []

services:
{services_config}
{autoscaling}{ingress}{dapr_config}{monitoring}
database:
  external: true
  connectionString: ""

kafka:
  enabled: true
  bootstrapServers: kafka:9092
  topics:
    taskEvents: "task-events"
    notifications: "notifications"

serviceAccount:
  create: true
  annotations: {{}}
  name: ""

podAnnotations: {{}}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

nodeSelector: {{}}

tolerations: []

affinity: {{}}
"""

def create_deployment_template(service_name: str, features: Dict[str, bool]) -> str:
    """Generate deployment template for a service."""
    safe_name = service_name.replace('-', '')

    dapr_annotations = ""
    if features.get("dapr", False):
        dapr_annotations = """        {{- if .Values.dapr.enabled }}
        dapr.io/enabled: "true"
        dapr.io/app-id: "{{ $serviceName }}"
        dapr.io/app-port: "{{ .Values.dapr.appPort }}"
        dapr.io/log-level: "{{ .Values.dapr.logLevel }}"
        {{- end }}"""

    return f"""{{{{- $serviceName := "{safe_name}" }}}}
{{{{- if index .Values.services $serviceName "enabled" }}}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "chart.fullname" . }}}}-{{{{ $serviceName }}}}
  labels:
    {{{{- include "chart.labels" . | nindent 4 }}}}
    app.kubernetes.io/component: {{{{ $serviceName }}}}
spec:
  {{{{- if not .Values.autoscaling.enabled }}}}
  replicas: {{{{ index .Values.services $serviceName "replicaCount" }}}}
  {{{{- end }}}}
  selector:
    matchLabels:
      {{{{- include "chart.selectorLabels" . | nindent 6 }}}}
      app.kubernetes.io/component: {{{{ $serviceName }}}}
  template:
    metadata:
      annotations:
        checksum/config: {{{{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}}}
        {{{{- with .Values.podAnnotations }}}}
        {{{{- toYaml . | nindent 8 }}}}
        {{{{- end }}}}{dapr_annotations}
      labels:
        {{{{- include "chart.selectorLabels" . | nindent 8 }}}}
        app.kubernetes.io/component: {{{{ $serviceName }}}}
    spec:
      {{{{- with .Values.global.imagePullSecrets }}}}
      imagePullSecrets:
        {{{{- toYaml . | nindent 8 }}}}
      {{{{- end }}}}
      serviceAccountName: {{{{ include "chart.serviceAccountName" . }}}}
      securityContext:
        {{{{- toYaml .Values.podSecurityContext | nindent 8 }}}}
      containers:
      - name: {{{{ $serviceName }}}}
        securityContext:
          {{{{- toYaml .Values.securityContext | nindent 12 }}}}
        image: "{{{{ .Values.global.registry }}}}/{{{{ index .Values.services $serviceName "image" "repository" }}}}:{{{{ index .Values.services $serviceName "image" "tag" }}}}"
        imagePullPolicy: {{{{ index .Values.services $serviceName "image" "pullPolicy" }}}}
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          {{{{- toYaml (index .Values.services $serviceName "resources") | nindent 12 }}}}
        env:
        - name: ENVIRONMENT
          value: {{{{ .Values.global.environment | quote }}}}
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{{{ include "chart.fullname" . }}}}-secrets
              key: database-url
        envFrom:
        - configMapRef:
            name: {{{{ include "chart.fullname" . }}}}-config
      {{{{- with .Values.nodeSelector }}}}
      nodeSelector:
        {{{{- toYaml . | nindent 8 }}}}
      {{{{- end }}}}
      {{{{- with .Values.affinity }}}}
      affinity:
        {{{{- toYaml . | nindent 8 }}}}
      {{{{- end }}}}
      {{{{- with .Values.tolerations }}}}
      tolerations:
        {{{{- toYaml . | nindent 8 }}}}
      {{{{- end }}}}
{{{{- end }}}}
"""

def create_service_template(service_name: str) -> str:
    """Generate service template."""
    safe_name = service_name.replace('-', '')

    return f"""{{{{- $serviceName := "{safe_name}" }}}}
{{{{- if index .Values.services $serviceName "enabled" }}}}
apiVersion: v1
kind: Service
metadata:
  name: {{{{ include "chart.fullname" . }}}}-{{{{ $serviceName }}}}
  labels:
    {{{{- include "chart.labels" . | nindent 4 }}}}
    app.kubernetes.io/component: {{{{ $serviceName }}}}
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: http
    protocol: TCP
    name: http
  selector:
    {{{{- include "chart.selectorLabels" . | nindent 4 }}}}
    app.kubernetes.io/component: {{{{ $serviceName }}}}
{{{{- end }}}}
"""

def create_hpa_template() -> str:
    """Generate HPA template."""
    return """{{- if .Values.autoscaling.enabled }}
{{- range $service, $config := .Values.autoscaling }}
{{- if ne $service "enabled" }}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "chart.fullname" $ }}-{{ $service }}
  labels:
    {{- include "chart.labels" $ | nindent 4 }}
    app.kubernetes.io/component: {{ $service }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "chart.fullname" $ }}-{{ $service }}
  minReplicas: {{ $config.minReplicas }}
  maxReplicas: {{ $config.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ $config.targetCPUUtilizationPercentage }}
{{- end }}
{{- end }}
{{- end }}
"""

def create_ingress_template() -> str:
    """Generate ingress template."""
    return """{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "chart.fullname" $ }}-{{ .service }}
                port:
                  number: 80
          {{- end }}
    {{- end }}
{{- end }}
"""

def create_helpers_tpl(app_name: str) -> str:
    """Generate _helpers.tpl template."""
    return f"""{{{{/*
Expand the name of the chart.
*/}}}}
{{{{- define "chart.name" -}}}}
{{{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{{{/*
Create a default fully qualified app name.
*/}}}}
{{{{- define "chart.fullname" -}}}}
{{{{- if .Values.fullnameOverride }}}}
{{{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- $name := default .Chart.Name .Values.nameOverride }}}}
{{{{- if contains $name .Release.Name }}}}
{{{{- .Release.Name | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}
{{{{- end }}}}
{{{{- end }}}}

{{{{/*
Create chart name and version as used by the chart label.
*/}}}}
{{{{- define "chart.chart" -}}}}
{{{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{{{/*
Common labels
*/}}}}
{{{{- define "chart.labels" -}}}}
helm.sh/chart: {{{{ include "chart.chart" . }}}}
{{{{ include "chart.selectorLabels" . }}}}
{{{{- if .Chart.AppVersion }}}}
app.kubernetes.io/version: {{{{ .Chart.AppVersion | quote }}}}
{{{{- end }}}}
app.kubernetes.io/managed-by: {{{{ .Release.Service }}}}
{{{{- end }}}}

{{{{/*
Selector labels
*/}}}}
{{{{- define "chart.selectorLabels" -}}}}
app.kubernetes.io/name: {{{{ include "chart.name" . }}}}
app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}

{{{{/*
Create the name of the service account to use
*/}}}}
{{{{- define "chart.serviceAccountName" -}}}}
{{{{- if .Values.serviceAccount.create }}}}
{{{{- default (include "chart.fullname" .) .Values.serviceAccount.name }}}}
{{{{- else }}}}
{{{{- default "default" .Values.serviceAccount.name }}}}
{{{{- end }}}}
{{{{- end }}}}
"""

def create_configmap_template() -> str:
    """Generate ConfigMap template."""
    return """apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "chart.fullname" . }}-config
  labels:
    {{- include "chart.labels" . | nindent 4 }}
data:
  KAFKA_BOOTSTRAP_SERVERS: {{ .Values.kafka.bootstrapServers | quote }}
  TASK_EVENTS_TOPIC: {{ .Values.kafka.topics.taskEvents | quote }}
  NOTIFICATIONS_TOPIC: {{ .Values.kafka.topics.notifications | quote }}
  {{- if .Values.dapr.enabled }}
  DAPR_ENABLED: "true"
  {{- end }}
"""

def create_secret_template() -> str:
    """Generate Secret template."""
    return """apiVersion: v1
kind: Secret
metadata:
  name: {{ include "chart.fullname" . }}-secrets
  labels:
    {{- include "chart.labels" . | nindent 4 }}
type: Opaque
data:
  database-url: {{ .Values.database.connectionString | b64enc | quote }}
"""

def create_serviceaccount_template() -> str:
    """Generate ServiceAccount template."""
    return """{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "chart.serviceAccountName" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
"""

def generate_helm_chart(
    app_name: str,
    output_dir: str,
    services: List[str],
    features: Dict[str, bool],
    version: str = "0.1.0"
):
    """Generate complete Helm chart structure."""
    chart_path = Path(output_dir) / app_name
    templates_path = chart_path / "templates"

    # Create directories
    chart_path.mkdir(parents=True, exist_ok=True)
    templates_path.mkdir(exist_ok=True)

    # Create Chart.yaml
    (chart_path / "Chart.yaml").write_text(create_chart_yaml(app_name, version))

    # Create values.yaml
    (chart_path / "values.yaml").write_text(create_values_yaml(services, features))

    # Create templates
    (templates_path / "_helpers.tpl").write_text(create_helpers_tpl(app_name))
    (templates_path / "configmap.yaml").write_text(create_configmap_template())
    (templates_path / "secret.yaml").write_text(create_secret_template())
    (templates_path / "serviceaccount.yaml").write_text(create_serviceaccount_template())

    if features.get("autoscaling", False):
        (templates_path / "hpa.yaml").write_text(create_hpa_template())

    if features.get("ingress", False):
        (templates_path / "ingress.yaml").write_text(create_ingress_template())

    # Create deployment and service for each service
    for service in services:
        safe_name = service.replace('-', '')
        (templates_path / f"deployment-{safe_name}.yaml").write_text(
            create_deployment_template(service, features)
        )
        (templates_path / f"service-{safe_name}.yaml").write_text(
            create_service_template(service)
        )

    # Create environment-specific values files
    create_env_values(chart_path, features)

    print(f"✅ Helm chart '{app_name}' generated at: {chart_path}")
    print(f"\nNext steps:")
    print(f"1. Review and customize values: {chart_path}/values.yaml")
    print(f"2. Lint the chart: helm lint {chart_path}")
    print(f"3. Install: helm install {app_name} {chart_path} --namespace <namespace> --create-namespace")

def create_env_values(chart_path: Path, features: Dict[str, bool]):
    """Create environment-specific values files."""
    # Development
    dev_values = """global:
  environment: development

services:
  backend:
    replicaCount: 1
  frontend:
    replicaCount: 1
  notificationservice:
    replicaCount: 1

autoscaling:
  enabled: false

ingress:
  tls: []
"""
    (chart_path / "values-dev.yaml").write_text(dev_values)

    # Staging
    staging_values = """global:
  environment: staging

services:
  backend:
    replicaCount: 2
  frontend:
    replicaCount: 2

autoscaling:
  enabled: true
  backend:
    minReplicas: 2
    maxReplicas: 10
"""
    (chart_path / "values-staging.yaml").write_text(staging_values)

    # Production
    prod_values = """global:
  environment: production

services:
  backend:
    replicaCount: 5
  frontend:
    replicaCount: 3

autoscaling:
  enabled: true
  backend:
    minReplicas: 5
    maxReplicas: 20
    targetCPUUtilizationPercentage: 75
  frontend:
    minReplicas: 3
    maxReplicas: 15
    targetCPUUtilizationPercentage: 80

monitoring:
  enabled: true
"""
    (chart_path / "values-prod.yaml").write_text(prod_values)

def main():
    parser = argparse.ArgumentParser(description="Generate Helm charts for Kubernetes deployment")
    parser.add_argument("app_name", help="Application name")
    parser.add_argument("--output", "-o", default="./helm", help="Output directory")
    parser.add_argument("--services", nargs="+",
                       default=["frontend", "backend", "notification-service"],
                       help="List of services")
    parser.add_argument("--autoscaling", action="store_true", help="Enable autoscaling")
    parser.add_argument("--ingress", action="store_true", help="Enable ingress")
    parser.add_argument("--tls", action="store_true", help="Enable TLS")
    parser.add_argument("--dapr", action="store_true", help="Enable Dapr")
    parser.add_argument("--monitoring", action="store_true", help="Enable monitoring")
    parser.add_argument("--version", default="0.1.0", help="Chart version")

    args = parser.parse_args()

    features = {
        "autoscaling": args.autoscaling,
        "ingress": args.ingress,
        "tls": args.tls,
        "dapr": args.dapr,
        "monitoring": args.monitoring
    }

    generate_helm_chart(
        app_name=args.app_name,
        output_dir=args.output,
        services=args.services,
        features=features,
        version=args.version
    )

if __name__ == "__main__":
    main()
