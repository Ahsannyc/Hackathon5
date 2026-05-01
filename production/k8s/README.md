# Kubernetes Deployment Manifests

**Status:** Placeholder for Exercise 2.7  
**Purpose:** Kubernetes manifests for production deployment

## Structure

```
k8s/
├── README.md (this file)
├── namespace.yaml
├── configmap.yaml
├── secrets.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
└── monitoring/
    ├── servicemonitor.yaml
    └── prometheusrule.yaml
```

## Deployment Steps (Exercise 2.7)

1. Create namespace: `kubectl apply -f namespace.yaml`
2. Create secrets: `kubectl apply -f secrets.yaml`
3. Create configmap: `kubectl apply -f configmap.yaml`
4. Deploy application: `kubectl apply -f deployment.yaml`
5. Expose service: `kubectl apply -f service.yaml`
6. Setup ingress: `kubectl apply -f ingress.yaml`
7. Monitor: `kubectl apply -f monitoring/`

**Next:** Will be populated in Exercise 2.7 - Kubernetes Deployment
