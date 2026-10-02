{{- range $project := .Values.projects }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $.Release.Name }}-{{ $project.name }}
  labels:
    app.kubernetes.io/name: {{ $project.name }}
    app.kubernetes.io/instance: {{ $.Release.Name }}
    app.kubernetes.io/component: ugc
    app.kubernetes.io/part-of: ugc-marketplace
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "{{ $project.service.targetPort | default $.Values.defaults.service.targetPort }}"
    prometheus.io/path: "/metrics"
spec:
  replicas: {{ $project.replicaCount | default $.Values.defaults.replicaCount }}
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ $project.name }}
      app.kubernetes.io/instance: {{ $.Release.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ $project.name }}
        app.kubernetes.io/instance: {{ $.Release.Name }}
        app.kubernetes.io/component: ugc
        app.kubernetes.io/part-of: ugc-marketplace
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{ $project.service.targetPort | default $.Values.defaults.service.targetPort }}"
        prometheus.io/path: "/metrics"
        checksum/config: {{ include (print $.Template.BasePath "/configmap.tpl") $ | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.tpl") $ | sha256sum }}
    spec:
      serviceAccountName: {{ $.Release.Name }}-{{ $project.name }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: {{ $project.name }}
          image: "{{ $.Values.global.imageRegistry }}/{{ $project.image.repository | default $.Values.defaults.image.repository }}:{{ $project.image.tag | default $.Values.defaults.image.tag }}"
          imagePullPolicy: {{ $project.image.pullPolicy | default $.Values.defaults.image.pullPolicy }}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          ports:
            - name: http
              containerPort: {{ $project.service.targetPort | default $.Values.defaults.service.targetPort }}
              protocol: TCP
            - name: metrics
              containerPort: 9090
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ $.Release.Name }}-{{ $project.name }}-config
            - secretRef:
                name: {{ $.Release.Name }}-{{ $project.name }}-secret
                optional: true
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: {{ $.Values.defaults.livenessProbe.initialDelaySeconds }}
            periodSeconds: {{ $.Values.defaults.livenessProbe.periodSeconds }}
            timeoutSeconds: {{ $.Values.defaults.livenessProbe.timeoutSeconds }}
            failureThreshold: {{ $.Values.defaults.livenessProbe.failureThreshold }}
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: {{ $.Values.defaults.readinessProbe.initialDelaySeconds }}
            periodSeconds: {{ $.Values.defaults.readinessProbe.periodSeconds }}
            timeoutSeconds: {{ $.Values.defaults.readinessProbe.timeoutSeconds }}
            failureThreshold: {{ $.Values.defaults.readinessProbe.failureThreshold }}
          startupProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: {{ $.Values.defaults.startupProbe.initialDelaySeconds }}
            periodSeconds: {{ $.Values.defaults.startupProbe.periodSeconds }}
            failureThreshold: {{ $.Values.defaults.startupProbe.failureThreshold }}
          resources:
            {{- toYaml ($project.resources | default $.Values.defaults.resources) | nindent 12 }}
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: cache
              mountPath: /cache
            - name: uploads
              mountPath: /uploads
      volumes:
        - name: tmp
          emptyDir: {}
        - name: cache
          emptyDir: {}
        - name: uploads
          emptyDir:
            sizeLimit: 1Gi
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: {{ $project.name }}
              app.kubernetes.io/instance: {{ $.Release.Name }}
{{- end }}
