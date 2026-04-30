# Task 6: Helm Migration for Monitoring Stack

This final step requires you to completely clean up the monitoring raw manifests you applied in Task 2, and then reinstall them using **Helm** (the Kubernetes Package Manager).

## 1. Clean Up Existing Raw Manifests
Run the following commands on your EC2 Master Node to delete the old resources:

```bash
# 1. Delete the Monitoring Stack (Prometheus, Loki, Grafana)
kubectl delete namespace monitoring

# 2. Delete the Kubernetes Dashboard
kubectl delete namespace kubernetes-dashboard
kubectl delete clusterrolebinding admin-user
kubectl delete clusterrole kubernetes-dashboard
```

Wait until the namespaces are fully deleted (this may take a minute). Check with:
```bash
kubectl get namespaces
```

---

## 2. Install Helm
If Helm is not already installed on your EC2 instance, install it:
```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
helm version
```

---

## 3. Reinstall with Helm

### A. Install Kubernetes Dashboard
```bash
# Add the repository
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm repo update

# Install Dashboard
helm install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --namespace kubernetes-dashboard --create-namespace

# Create admin user again to get the login token
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Get Login Token
kubectl -n kubernetes-dashboard create token admin-user

# Port forward or change service type to NodePort to access it
kubectl patch svc kubernetes-dashboard-kong-proxy -n kubernetes-dashboard -p '{"spec": {"type": "NodePort"}}'
```

### B. Install Prometheus, Loki, and Grafana Stack
The easiest way to get Prometheus, Loki, and Grafana working together via Helm is using the `kube-prometheus-stack` and adding Loki.

```bash
# Add repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus & Grafana (combined chart)
helm install prom-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

# Install Loki
helm install loki grafana/loki-stack --namespace monitoring --set grafana.enabled=false

# Expose Grafana to access it
kubectl patch svc prom-stack-grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'
```

**Connect as before:**
1. Check Grafana's NodePort: `kubectl get svc prom-stack-grafana -n monitoring`
2. Default login for the Helm chart is usually `admin` / `prom-operator`.
3. Go to **Connections > Data sources**. Prometheus will usually be added automatically by the chart!
4. Add **Loki**. Set URL to: `http://loki:3100` and save.

**Congratulations! All AWS K8s assignment tasks are now complete.**
