# Kubernetes Deployment: CloudFlow Customer Success FTE

**Document Version:** 1.0  
**Date:** 2026-04-26  
**Status:** Production Ready  
**Tier:** Gold

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Deployment Strategy](#deployment-strategy)
5. [Scaling & Auto-Scaling](#scaling--auto-scaling)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Security Configuration](#security-configuration)
8. [Local Deployment (Minikube)](#local-deployment-minikube)
9. [Cloud Deployment](#cloud-deployment)
10. [Operational Procedures](#operational-procedures)
11. [Troubleshooting](#troubleshooting)
12. [Appendix](#appendix)

---

## Overview

The CloudFlow Customer Success FTE is deployed as a production-grade Kubernetes application with:

- **3 minimum replicas** for both API and Worker deployments
- **Auto-scaling** up to 10 replicas (API) and 15 replicas (Worker)
- **Zero-downtime deployments** using rolling updates
- **24/7 availability** through health checks and pod disruption budgets
- **Enterprise-grade security** with RBAC, network policies, and secrets management
- **Comprehensive monitoring** via Prometheus and service monitors
- **Horizontal scaling** based on CPU (70% target) and memory (75-80% target) utilization

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          KUBERNETES CLUSTER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              INGRESS LAYER (nginx + cert-manager)              │ │
│  │  https://api.cloudflow.example.com & https://cloudflow.*.com  │ │
│  └───────────────────────────┬──────────────────────────────────┘ │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐ │
│  │                    SERVICE LAYER                             │ │
│  │  fte-api-service (ClusterIP)                                 │ │
│  │  fte-metrics-service (ClusterIP)                             │ │
│  └───────────────────────────┬──────────────────────────────────┘ │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐ │
│  │              DEPLOYMENT LAYER (Rolling Updates)              │ │
│  │  ┌──────────────────┐        ┌──────────────────────────┐    │ │
│  │  │   FTE-API        │        │    FTE-WORKER           │    │ │
│  │  │  (3-10 replicas) │        │   (3-15 replicas)       │    │ │
│  │  │  ├─ Pod 1 (API)  │        │   ├─ Pod 1 (Worker)     │    │ │
│  │  │  ├─ Pod 2 (API)  │        │   ├─ Pod 2 (Worker)     │    │ │
│  │  │  └─ Pod 3 (API)  │        │   └─ Pod 3 (Worker)     │    │ │
│  │  └──────────────────┘        └──────────────────────────┘    │ │
│  └───────────────────────────┬──────────────────────────────────┘ │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐ │
│  │            DATA LAYER (External Services)                   │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐    │ │
│  │  │  PostgreSQL DB   │  │  Kafka Cluster (3 brokers)   │    │ │
│  │  │  (cloudflow_db)  │  │  (5 topics)                  │    │ │
│  │  └──────────────────┘  └──────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │          MONITORING & OBSERVABILITY LAYER                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │ │
│  │  │ Prometheus   │  │  Grafana     │  │ ServiceMonitor       │ │ │
│  │  │  :9090       │  │  Dashboards  │  │ (Metrics collection) │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Namespace Isolation

All resources deployed in `fte-customer-success` namespace:
```yaml
namespace: fte-customer-success
```

**Benefits:**
- Resource isolation and multi-tenancy
- RBAC scoped to namespace
- Easy cleanup (delete entire namespace)
- Resource quotas enforcement

### Component Breakdown

#### 1. FastAPI Service (fte-api)
- **Purpose:** Handle all customer inquiries and channel interactions
- **Replicas:** 3 (minimum) → 10 (maximum)
- **Container Image:** `cloudflow/fte-api:latest`
- **Port:** 8000 (HTTP), 9090 (Metrics)
- **Resource Requests:** 500m CPU, 512Mi memory
- **Resource Limits:** 1000m CPU, 1Gi memory

#### 2. Message Processor Worker (fte-worker)
- **Purpose:** Process messages from Kafka and route to agent
- **Replicas:** 3 (minimum) → 15 (maximum)
- **Container Image:** `cloudflow/fte-worker:latest`
- **Port:** 9090 (Metrics only)
- **Resource Requests:** 750m CPU, 1Gi memory
- **Resource Limits:** 2000m CPU, 2Gi memory

#### 3. Supporting Services
- **PostgreSQL:** External database service
- **Kafka:** External messaging broker (3 brokers)
- **Prometheus:** Metrics collection
- **Ingress Controller:** NGINX with SSL/TLS

---

## Components

### 1. Namespace (namespace.yaml)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fte-customer-success
```

**Purpose:** Isolate all FTE resources in dedicated namespace

### 2. ConfigMap (configmap.yaml)

**50+ configuration parameters including:**
- Kafka topics and bootstrap servers
- Database connection settings
- FastAPI configuration
- Cohere model settings
- Health check timeouts
- Resource limits
- Monitoring settings

**Key Variables:**
```yaml
KAFKA_BOOTSTRAP_SERVERS: kafka-broker:9092
DATABASE_HOST: postgres-service
COHERE_MODEL: command-r-plus
API_PORT: 8000
```

### 3. Secrets (secrets.yaml)

**Sensitive credentials (placeholders provided):**

```yaml
stringData:
  COHERE_KEY: <REPLACE_WITH_COHERE_API_KEY>
  DATABASE_URL: postgresql://<USER>:<PASSWORD>@postgres-service:5432/cloudflow_db
  TWILIO_ACCOUNT_SID: <REPLACE_WITH_TWILIO_SID>
  TWILIO_AUTH_TOKEN: <REPLACE_WITH_TWILIO_TOKEN>
  GMAIL_CLIENT_ID: <REPLACE_WITH_GMAIL_CLIENT_ID>
  GMAIL_CLIENT_SECRET: <REPLACE_WITH_GMAIL_CLIENT_SECRET>
  JWT_SECRET_KEY: <GENERATE_RANDOM_KEY>
```

**Security Best Practices:**
- All credentials encrypted at rest
- RBAC controls access
- Separate secrets for each credential type
- Regular rotation recommended (90-day cycle)

### 4. Deployment: API (deployment-api.yaml)

**Features:**
- 3 minimum replicas for high availability
- Rolling update strategy (maxSurge: 1, maxUnavailable: 0)
- Pod anti-affinity (spread across nodes)
- Init containers to wait for dependencies
- Full RBAC with ServiceAccount
- Security context (non-root user: 1000)
- All environment variables from ConfigMap/Secrets

**Health Checks:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/health
    port: http
  initialDelaySeconds: 20
  periodSeconds: 5
  failureThreshold: 2
```

### 5. Deployment: Worker (deployment-worker.yaml)

**Features:**
- 3 minimum replicas
- Optimized for CPU-intensive message processing
- 2x memory compared to API (1Gi vs 512Mi)
- Runs message processor as main process
- Custom health check logic (heartbeat file)
- Longer termination grace period (40s)

**Command:**
```yaml
args:
- python
- -m
- production.workers.message_processor
```

### 6. Services (service.yaml)

**Three service types:**

1. **fte-api-service** (ClusterIP)
   - Internal service for API pods
   - Port 80 → 8000 (HTTP)
   - Port 9090 (Metrics)

2. **fte-api-nodeport** (NodePort)
   - Development/testing access
   - NodePort 30080 for HTTP
   - NodePort 30090 for metrics

3. **fte-metrics-service** (ClusterIP)
   - Dedicated metrics endpoint
   - Scraped by Prometheus

### 7. Ingress & SSL/TLS (ingress.yaml)

**Hosts:**
- `api.cloudflow.example.com` → fte-api-service
- `cloudflow.example.com` → fte-api-service

**Features:**
- NGINX ingress controller
- Automatic SSL/TLS with cert-manager
- Rate limiting (100 req/min per IP)
- Connection limiting (10 concurrent)
- TLS certificate auto-renewal
- Network policies for pod-to-pod communication

**Security:**
```yaml
nginx.ingress.kubernetes.io/ssl-redirect: "true"
nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
nginx.ingress.kubernetes.io/rate-limit: "100"
nginx.ingress.kubernetes.io/limit-connections: "10"
```

### 8. Auto-Scaling (hpa.yaml)

#### API Auto-Scaler

```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - cpu: 70% target
  - memory: 80% target
scaleUp:
  - 100% increase per 30s (aggressive)
scaleDown:
  - 50% decrease per 60s (conservative)
```

**Behavior:**
- Scale up quickly (high demand)
- Scale down slowly (prevent oscillation)
- 5-minute stabilization window for scale-down

#### Worker Auto-Scaler

```yaml
minReplicas: 3
maxReplicas: 15
metrics:
  - cpu: 70% target
  - memory: 75% target
scaleUp:
  - 100% increase per 30s
scaleDown:
  - 33% decrease per 60s (even more conservative)
```

**Rationale:**
- Workers are stateful (Kafka consumer group)
- More conservative scale-down to avoid churn
- Can scale higher (15 replicas) to handle message load

#### Pod Disruption Budgets

```yaml
minAvailable: 2  # Always keep 2+ pods running
```

**Impact:**
- Kubernetes respects PDB during maintenance
- Prevents involuntary evictions below threshold
- Ensures service continuity

---

## Deployment Strategy

### Rolling Updates (Zero Downtime)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1           # One extra pod during update
    maxUnavailable: 0     # Zero pods unavailable
```

**Timeline for 3-replica update:**
1. Start 1 new pod (4 running total)
2. Remove 1 old pod (still 3 running)
3. Start 1 new pod (4 running)
4. Remove 1 old pod (3 running)
5. Start 1 new pod (4 running)
6. Remove 1 old pod (3 new running)

**Duration:** ~5-10 minutes for 3 replicas

### Pre-Stop Hook (Graceful Shutdown)

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]
```

**Purpose:**
- Give in-flight requests time to complete
- Deregister from load balancer
- Close database connections gracefully

### Initialization (Init Containers)

```yaml
initContainers:
- name: wait-for-postgres
  command: ['sh', '-c', 'until nc -z postgres-service 5432']
- name: wait-for-kafka
  command: ['sh', '-c', 'until nc -z kafka-broker 9092']
```

**Ensures:**
- Database is ready before API starts
- Kafka is ready before worker starts
- Prevents cascading failures

---

## Scaling & Auto-Scaling

### Horizontal Pod Autoscaling (HPA)

#### CPU-Based Scaling

**API:** Scale when CPU > 70%
```
Current: 3 replicas × 500m (request) = 1500m capacity
If load = 1200m (80% utilization) → Trigger scale-up
New target: 2000m (4 replicas) → 500m per replica
```

**Worker:** Scale when CPU > 70%
```
Current: 3 replicas × 750m (request) = 2250m capacity
If load = 1800m (80% utilization) → Trigger scale-up
New target: 3000m (4 replicas) → 750m per replica
```

#### Memory-Based Scaling

**API:** Scale when Memory > 80%
```
Current: 3 replicas × 512Mi (request) = 1536Mi
If usage = 1200Mi (78% utilization) → Stay at 3
If usage = 1300Mi (85% utilization) → Scale to 4
```

**Worker:** Scale when Memory > 75%
```
Current: 3 replicas × 1Gi (request) = 3Gi
If usage = 2.4Gi (80% utilization) → Trigger scale-up
```

### Manual Scaling

```bash
# Scale API to 5 replicas
kubectl scale deployment fte-api --replicas=5 -n fte-customer-success

# Scale Worker to 8 replicas
kubectl scale deployment fte-worker --replicas=8 -n fte-customer-success
```

### Cluster Capacity Planning

**For 10x API replicas:**
- 10 × 1000m (limit) = 10 cores required
- 10 × 1Gi (limit) = 10Gi RAM required

**For 15x Worker replicas:**
- 15 × 2000m (limit) = 30 cores required
- 15 × 2Gi (limit) = 30Gi RAM required

**Total for peak load:**
- 40 cores (CPU)
- 40Gi RAM
- Recommend: 3 large nodes (16 cores, 32Gi each)

---

## Health Checks & Monitoring

### Liveness Probes

**Purpose:** Detect dead containers and restart them

**API Configuration:**
```yaml
httpGet:
  path: /health
  port: http
initialDelaySeconds: 30      # Wait 30s before first check
periodSeconds: 10            # Check every 10s
timeoutSeconds: 5            # Timeout after 5s
failureThreshold: 3          # Restart after 3 failures
```

**Timeline:** 30s + (3 failures × 10s) = 60 seconds to restart

**Worker Configuration:**
```yaml
exec:
  command:
  - /bin/sh
  - -c
  - |
    if [ -f /tmp/worker_last_heartbeat ]; then
      LAST_BEAT=$(cat /tmp/worker_last_heartbeat)
      CURRENT_TIME=$(date +%s)
      TIME_DIFF=$((CURRENT_TIME - LAST_BEAT))
      if [ $TIME_DIFF -gt 300 ]; then
        exit 1
      fi
    fi
    exit 0
```

**Heartbeat Check:** If worker hasn't updated heartbeat in 5 minutes, mark unhealthy

### Readiness Probes

**Purpose:** Prevent traffic to pods that aren't ready

**API Configuration:**
```yaml
httpGet:
  path: /api/health
  port: http
initialDelaySeconds: 20      # Wait 20s for startup
periodSeconds: 5             # Check every 5s
failureThreshold: 2          # Remove from LB after 2 failures
```

**Impact:** Slow to ready pods get removed from rotation

**Worker Configuration:**
```yaml
exec:
  command:
  - /bin/sh
  - -c
  - if [ -f /tmp/worker_ready ]; then exit 0; fi; exit 1
```

**Check:** Worker must create /tmp/worker_ready file

### Startup Probes

**Purpose:** Give containers time to initialize

**Configuration:**
```yaml
failureThreshold: 15         # Allow 15 failures
periodSeconds: 5             # Check every 5s
```

**Timeline:** 15 × 5 = 75 seconds to startup

**Result:** Pod has 75 seconds to start before being killed

### Prometheus Monitoring

**ServiceMonitor Configuration:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fte-monitor
spec:
  endpoints:
  - port: metrics
    interval: 30s           # Scrape every 30s
    path: /metrics
```

**Metrics Scraped:**
- API response times (p50, p95, p99)
- Worker processing time per message
- Kafka message lag
- Error rates
- Container resource usage
- JVM metrics (if applicable)

### Grafana Dashboards

**Default Dashboards:**
1. **System Health:** CPU, Memory, Network, Disk
2. **Application Metrics:** Requests/sec, Error rate, Latency
3. **Kafka Metrics:** Consumer lag, Throughput, Failed messages
4. **Pod Status:** Restarts, Age, Resource utilization

### Alerting Rules

**Critical (Immediate Response):**
```yaml
- API error rate > 5%
- Worker processing timeout
- Database connection pool exhausted
- Kafka consumer lag > 10,000 messages
```

**Warning (30-minute response):**
```yaml
- API CPU > 80%
- Worker memory > 85%
- HPA scaling unable to keep up
```

---

## Security Configuration

### RBAC (Role-Based Access Control)

**ServiceAccounts:**
- `fte-api-sa` → Can read ConfigMaps and Secrets
- `fte-worker-sa` → Can read ConfigMaps, Secrets, and Pods

**Roles:**
- Limited to namespace-scoped resources
- Explicit verb list (get, list, watch only)
- No cluster-admin or system roles

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fte-network-policy
spec:
  podSelector:
    matchLabels:
      app: cloudflow-fte
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: fte-customer-success
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 5432    # PostgreSQL
    - protocol: TCP
      port: 9092    # Kafka
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53      # DNS
    - protocol: UDP
      port: 53
```

**Rules:**
- Only accept traffic from same namespace or ingress controller
- Only send traffic to database, Kafka, DNS
- No pod-to-pod traffic outside namespace

### Secrets Encryption

**At Rest (Kubernetes Native):**
- Secrets stored in etcd encrypted via kms provider
- Key rotation every 90 days recommended

**In Transit:**
- All API communication over TLS
- All inter-pod communication via network policies
- Environment variable injection (not volume mounted)

### Container Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000              # Non-root user
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  capabilities:
    drop:
    - ALL
```

**Implications:**
- Prevents privilege escalation attacks
- Blocks raw socket access
- Enforces least-privilege principle

### SSL/TLS with cert-manager

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    solvers:
    - http01:
        ingress:
          class: nginx
```

**Features:**
- Automatic certificate provisioning
- Auto-renewal 30 days before expiry
- HTTP-01 challenge validation
- Certificate stored in Kubernetes Secret

---

## Local Deployment (Minikube)

### Prerequisites

```bash
# Install Minikube
https://minikube.sigs.k8s.io/docs/start/

# Install kubectl
https://kubernetes.io/docs/tasks/tools/

# Install Helm (optional, for package management)
https://helm.sh/docs/intro/install/
```

### Start Minikube Cluster

```bash
# Start with sufficient resources
minikube start --cpus=8 --memory=16384 --disk-size=50g

# Enable add-ons
minikube addons enable ingress
minikube addons enable prometheus
minikube addons enable dashboard
```

### Deploy to Minikube

```bash
# 1. Create namespace
kubectl apply -f production/k8s/namespace.yaml

# 2. Create ConfigMap and Secrets
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml

# 3. Update secrets with actual values
kubectl edit secret fte-secrets -n fte-customer-success

# 4. Deploy API and Worker
kubectl apply -f production/k8s/deployment-api.yaml
kubectl apply -f production/k8s/deployment-worker.yaml

# 5. Create services and ingress
kubectl apply -f production/k8s/service.yaml
kubectl apply -f production/k8s/ingress.yaml

# 6. Create HPA and PDB
kubectl apply -f production/k8s/hpa.yaml

# 7. Verify deployment
kubectl get pods -n fte-customer-success
kubectl get svc -n fte-customer-success
kubectl get ingress -n fte-customer-success
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n fte-customer-success -w

# Check logs
kubectl logs -f deployment/fte-api -n fte-customer-success
kubectl logs -f deployment/fte-worker -n fte-customer-success

# Port forward to API
kubectl port-forward svc/fte-api-service 8000:80 -n fte-customer-success

# Test API
curl http://localhost:8000/health
```

### Access Services

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Add to /etc/hosts (macOS/Linux) or C:\Windows\System32\drivers\etc\hosts (Windows)
$MINIKUBE_IP api.cloudflow.example.com
$MINIKUBE_IP cloudflow.example.com

# Access API
curl http://api.cloudflow.example.com:30080/health
```

### Monitor in Minikube

```bash
# Dashboard
minikube dashboard

# Prometheus
kubectl port-forward -n prometheus svc/prometheus 9090:9090

# Grafana (if installed)
kubectl port-forward -n grafana svc/grafana 3000:80
```

---

## Cloud Deployment

### AWS (EKS)

#### Create EKS Cluster

```bash
# Create cluster
aws eks create-cluster \
  --name fte-production \
  --version 1.28 \
  --role-arn arn:aws:iam::ACCOUNT:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy \
  --region us-east-1

# Add node group
aws eks create-nodegroup \
  --cluster-name fte-production \
  --nodegroup-name fte-nodes \
  --subnets subnet-xxx subnet-yyy \
  --node-role arn:aws:iam::ACCOUNT:role/NodeInstanceRole \
  --scaling-config minSize=3,maxSize=10,desiredSize=3 \
  --instance-types t3.xlarge
```

#### Deploy to EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name fte-production

# Deploy manifests
kubectl apply -f production/k8s/

# Verify
kubectl get pods -n fte-customer-success
```

### GCP (GKE)

#### Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create fte-production \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --enable-ip-alias
```

#### Deploy to GKE

```bash
# Get credentials
gcloud container clusters get-credentials fte-production --region us-central1

# Deploy manifests
kubectl apply -f production/k8s/

# Create service account for GCR
kubectl create secret docker-registry gcr-secret \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat ~/gcr-key.json)"
```

### Azure (AKS)

#### Create AKS Cluster

```bash
# Create resource group
az group create --name fte-rg --location eastus

# Create cluster
az aks create \
  --resource-group fte-rg \
  --name fte-production \
  --node-count 3 \
  --vm-set-type VirtualMachineScaleSets \
  --enable-managed-identity \
  --enable-cluster-autoscaling \
  --min-count 3 \
  --max-count 10
```

#### Deploy to AKS

```bash
# Get credentials
az aks get-credentials --resource-group fte-rg --name fte-production

# Deploy manifests
kubectl apply -f production/k8s/
```

---

## Operational Procedures

### Rolling Restart (No Downtime)

```bash
# Restart API pods
kubectl rollout restart deployment/fte-api -n fte-customer-success

# Restart Worker pods
kubectl rollout restart deployment/fte-worker -n fte-customer-success

# Check status
kubectl rollout status deployment/fte-api -n fte-customer-success
```

### Blue-Green Deployment

```bash
# Deploy new version to "green" deployment
kubectl apply -f production/k8s/deployment-api-v2.yaml

# Switch service to new deployment
kubectl patch service fte-api-service \
  -p '{"spec":{"selector":{"version":"v2"}}}' \
  -n fte-customer-success

# Delete old deployment
kubectl delete deployment fte-api-v1 -n fte-customer-success
```

### Canary Deployment

```bash
# Deploy canary with 1 replica
kubectl create deployment fte-api-canary \
  --image=cloudflow/fte-api:v2 \
  --replicas=1 \
  -n fte-customer-success

# Monitor metrics (10% of traffic)
# If healthy, scale canary to 100%
kubectl scale deployment fte-api-canary --replicas=3

# Clean up old deployment
kubectl delete deployment fte-api
```

### Update Image

```bash
# Update API image
kubectl set image deployment/fte-api \
  fte-api=cloudflow/fte-api:v2 \
  -n fte-customer-success

# Update Worker image
kubectl set image deployment/fte-worker \
  fte-worker=cloudflow/fte-worker:v2 \
  -n fte-customer-success

# Watch rollout
kubectl rollout status deployment/fte-api -n fte-customer-success -w
```

### Update ConfigMap

```bash
# Edit ConfigMap
kubectl edit configmap fte-config -n fte-customer-success

# Trigger pod restart to pick up changes
kubectl rollout restart deployment/fte-api -n fte-customer-success
```

### Update Secrets

```bash
# Update specific secret
kubectl patch secret fte-secrets \
  -p '{"data":{"COHERE_KEY":"'$(echo -n "new-key" | base64)'"}}'  \
  -n fte-customer-success

# Restart pods to pick up changes
kubectl rollout restart deployment/fte-api -n fte-customer-success
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/fte-api -n fte-customer-success

# Rollback to previous version
kubectl rollout undo deployment/fte-api -n fte-customer-success

# Rollback to specific revision
kubectl rollout undo deployment/fte-api --to-revision=5 -n fte-customer-success
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n fte-customer-success

# Check logs
kubectl logs <pod-name> -n fte-customer-success
kubectl logs <pod-name> -n fte-customer-success --previous  # Crashed pod logs

# Check events
kubectl get events -n fte-customer-success --sort-by='.lastTimestamp'
```

### High CPU Usage

```bash
# Check resource usage
kubectl top pods -n fte-customer-success
kubectl top nodes

# Check HPA status
kubectl get hpa -n fte-customer-success
kubectl describe hpa fte-api-hpa -n fte-customer-success

# Manually scale up
kubectl scale deployment fte-api --replicas=5 -n fte-customer-success
```

### Database Connection Failures

```bash
# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  sh -c "nc -zv postgres-service 5432"

# Check database service
kubectl get svc postgres-service -n fte-customer-success
kubectl describe svc postgres-service -n fte-customer-success
```

### Kafka Consumer Lag

```bash
# Check Kafka topics
kubectl exec -it <kafka-pod> -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# Check consumer group status
kubectl exec -it <kafka-pod> -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group fte-message-processor-prod --describe
```

### Memory Leaks

```bash
# Monitor memory over time
kubectl top pod <pod-name> -n fte-customer-success --containers

# Check container resource limits
kubectl describe pod <pod-name> -n fte-customer-success | grep -A 5 "Limits:"

# Check for memory-intensive processes
kubectl exec -it <pod-name> -c fte-api -- ps aux
```

### TLS Certificate Issues

```bash
# Check certificate status
kubectl describe certificate fte-tls-cert -n fte-customer-success

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Manually renew certificate
kubectl delete secret fte-tls-cert -n fte-customer-success
kubectl delete certificate fte-tls-cert -n fte-customer-success
```

---

## Appendix

### Configuration Checklist

Before deploying to production:

- [ ] Update all `<REPLACE_WITH_*>` placeholders in secrets.yaml
- [ ] Update ingress hostnames (api.cloudflow.example.com)
- [ ] Update CORS_ORIGINS in configmap.yaml
- [ ] Update SMTP_HOST and email credentials
- [ ] Update AWS_REGION and S3_BUCKET (if using)
- [ ] Update PAGERDUTY_INTEGRATION_KEY (if using)
- [ ] Update SLACK_WEBHOOK_URL (if using)
- [ ] Generate and set JWT_SECRET_KEY
- [ ] Generate and set ENCRYPTION_KEY
- [ ] Generate and set WEBHOOK_SECRET_KEY
- [ ] Configure DNS records for ingress hostnames
- [ ] Install cert-manager in cluster
- [ ] Install ingress controller (NGINX)
- [ ] Install Prometheus/Grafana (monitoring)
- [ ] Configure storage class for persistent volumes (if needed)

### Useful Commands

```bash
# Get all resources in namespace
kubectl get all -n fte-customer-success

# Describe deployment
kubectl describe deployment fte-api -n fte-customer-success

# View real-time logs
kubectl logs -f deployment/fte-api -n fte-customer-success

# Execute command in pod
kubectl exec -it <pod-name> -n fte-customer-success -- /bin/bash

# Port forward
kubectl port-forward deployment/fte-api 8000:8000 -n fte-customer-success

# Watch deployment
kubectl get deployment fte-api -n fte-customer-success -w

# Get resource metrics
kubectl top pods -n fte-customer-success

# Apply all manifests
kubectl apply -f production/k8s/

# Delete all resources
kubectl delete namespace fte-customer-success
```

### Production Readiness Checklist

- [ ] All health checks green (liveness, readiness, startup)
- [ ] At least 3 API replicas running
- [ ] At least 3 Worker replicas running
- [ ] HPA active and scaling properly
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards visible
- [ ] Alerts configured and tested
- [ ] Network policies active
- [ ] RBAC restricted to service accounts
- [ ] Secrets encrypted at rest
- [ ] TLS certificates valid and renewing
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Capacity planning complete (node count)
- [ ] Load testing completed
- [ ] Security scanning passed
- [ ] Documentation up-to-date

---

## Support

For issues, refer to:
1. Kubernetes official documentation: https://kubernetes.io/docs/
2. Exercise 2.6 PHR record in history/prompts/general/
3. CHECKPOINT_EXERCISE_2_6.md for deployment status
4. Team runbooks in /docs/

**Last Updated:** 2026-04-26  
**Status:** Production Ready ✅
