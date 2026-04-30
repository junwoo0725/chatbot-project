# Task 4 & 5: Kubernetes Resiliency & Rolling Updates

These tasks require you to interact with the cluster to verify its self-healing capabilities and zero-downtime deployments.

## Task 4: Resiliency Validation (Pod Recreation)
The Deployments you applied in Task 3 have `replicas: 2`. This means Kubernetes will constantly monitor to ensure exactly 2 pods are running.

**Steps to verify:**
1. List the pods and identify one to delete:
   ```bash
   kubectl get pods
   ```
   *Note: You should see 2 pods for `community-be` and 2 for `community-fe`.*

2. Delete one of the running pods (replace `<pod-name>` with an actual name from step 1):
   ```bash
   kubectl delete pod <pod-name>
   ```

3. Immediately check the pods again. You should see a terminating pod and a brand new pod starting up simultaneously (ContainerCreating):
   ```bash
   kubectl get pods -w
   ```
   *(Press Ctrl+C to stop watching once the new pod is Running)*

4. **Verify in Dashboard/Grafana:**
   - Go to your **Kubernetes Dashboard**. Navigate to **Workloads > Pods**. You will see the event history showing the pod death and recreation.
   - Go to **Grafana > Explore** (select Loki source), and query `{app="community-be"}` or examine the kubelet system logs to see the scheduling of the new pod.

---

## Task 5: Rolling Update Validation (Zero Downtime)
You will simulate a new version rollout for your Backend (or Frontend).

**Steps to verify:**
1. Open your `be-deployment.yaml` (or `fe-deployment.yaml`).
2. Change the `image` field line. For example, change:
   `image: junwoo0725/community-be:latest`
   to a different tag (e.g., build a new Docker image and push it as `v2` or `latest-v2`):
   `image: junwoo0725/community-be:v2`
3. Apply the updated configuration:
   ```bash
   kubectl apply -f k8s/assignments/be-deployment.yaml
   ```
4. Watch the rolling update in real-time. Because of the default RollingUpdate strategy and the ReadinessProbes we configured, Kubernetes will spin up new pods. It waits for them to pass the ReadinessProbe (`/health`) before it terminates the old pods.
   ```bash
   kubectl get pods -w
   # OR
   kubectl rollout status deployment/community-be
   ```
   *(You'll see messages like: "Waiting for deployment "community-be" rollout to finish: 1 out of 2 new replicas have been updated...")*

By observing that requests to your service remain uninterrupted while old pods are swapped for new ones, you prove the Rolling Update is working as intended!
