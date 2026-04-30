# Task 2: Monitoring & Dashboard Setup (Raw Manifests)

## 1. Kubernetes Dashboard Installation

To install the Kubernetes Dashboard using the official raw manifests, run exactly these commands on your EC2 Master Node:

```bash
# 1. Apply the official Kubernetes Dashboard manifest
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# 2. Create the admin ServiceAccount and ClusterRoleBinding to access the dashboard
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

# 3. Get the Bearer Token to log in (Save this token temporarily!)
kubectl -n kubernetes-dashboard create token admin-user

# 4. Expose Dashboard (Change Service type from ClusterIP to NodePort)
kubectl patch svc kubernetes-dashboard -n kubernetes-dashboard -p '{"spec": {"type": "NodePort"}}'
# To find the assigned NodePort (30000-32767), run:
kubectl get svc kubernetes-dashboard -n kubernetes-dashboard
```

## 2. Prometheus, Loki, and Grafana Installation

Because Task 6 specifically requires migrating *from* raw manifests *to* Helm, we will install highly simplified raw manifest versions of Prometheus, Loki, and Grafana here for Task 2. This satisfies the "without Helm initially" requirement and sets up the teardown scenario for Task 6.

### Creating the Monitoring Stack
Copy the following command block and execute it directly on the EC2 Master Node:

```bash
# 1. Create a namespace
kubectl create namespace monitoring

# 2. Create a basic Prometheus deployment
cat <<EOF | kubectl apply -n monitoring -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
        - role: endpoints
EOF

cat <<EOF | kubectl apply -n monitoring -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        args:
          - "--config.file=/etc/prometheus/prometheus.yml"
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config-volume
          mountPath: /etc/prometheus
      volumes:
      - name: config-volume
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
spec:
  type: ClusterIP
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
EOF

# 3. Create a basic Loki deployment
cat <<EOF | kubectl apply -n monitoring -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
      - name: loki
        image: grafana/loki:2.9.0
        ports:
        - containerPort: 3100
---
apiVersion: v1
kind: Service
metadata:
  name: loki-service
spec:
  type: ClusterIP
  selector:
    app: loki
  ports:
    - port: 3100
      targetPort: 3100
EOF

# 4. Create a basic Grafana deployment
cat <<EOF | kubectl apply -n monitoring -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.0.3
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
spec:
  type: NodePort
  selector:
    app: grafana
  ports:
    - port: 3000
      targetPort: 3000
EOF
```

## 3. Connecting Prometheus and Loki to Grafana
1. Run `kubectl get svc grafana-service -n monitoring` to find Grafana's assigned **NodePort**.
2. Assuming your EC2 has the correct security groups open, go to `http://<EC2-Public-IP>:<NodePort>` in your browser.
3. Log in with the default credentials (`admin` / `admin`).
4. Go to **Connections > Data Sources > Add data source**.
5. Add **Prometheus**. Set the URL to: `http://prometheus-service.monitoring.svc.cluster.local:9090` and save.
6. Add **Loki**. Set the URL to: `http://loki-service.monitoring.svc.cluster.local:3100` and save.

This fully satisfies Task 2!
