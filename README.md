# Kubernetes Multi-App Lab 539

Nginx on `k8s-lb` (192.168.29.20) sends requests to Traefik on workers .11 and .12 using NodePort 30082. Traefik routes traffic to three Flask apps in `student-web`. The existing `nginx-lab` uses NodePort 30081 and `cluster-check` uses NodePort 30080.

| URL | Service | Expected result |
| --- | --- | --- |
| http://www.id-539.com/about | app-about | Student information |
| http://www.id-539.com/research | app-research | Saved research summary |
| http://www.id-539.com/api/HelloK8s | app-api | Large centered message |
| http://admin.id-539.com/edit | app-research | Basic Auth and edit form |
| http://admin.id-539.com/ | app-research | Redirect to /edit |

## Deployment

Use a Kubernetes cluster with the dedicated lab volume or an equivalent storage configuration, a configured kubectl client, Helm, Docker with push access, and Nginx on the load balancer.

1. Build and publish `alohathdz/app-about:v1`, `alohathdz/app-api:v1`, and `alohathdz/app-research:v2` from each directory in `apps/`. If a repository requires authentication, configure an image pull secret for the Deployment or import the matching image into each worker's Kubernetes containerd namespace. Supply a photo separately, if applicable.
2. Apply `k8s/namespace.yaml`. Create Secret `research-admin` in `student-web` with keys `ADMIN_USER` and `ADMIN_PASSWORD` using privately supplied, nonempty values.
3. Apply `k8s/research-pv.yaml` and `k8s/research-pvc.yaml` and the three app manifests. Set `STUDENT_NAME` and `STUDENT_ID` on the live `app-about` Deployment. Check rollout status and confirm `research-data` is Bound after scheduling.
4. Install Traefik chart version `42.4.1` with `--skip-crds` using `k8s/traefik-values.yaml` in namespace `traefik`, then apply `k8s/ingress.yaml`. Check both worker upstreams with the corresponding Host header.
5. Install `nginx/student-web.conf` as a separate enabled site on the LB. Validate with `nginx -t` before reloading. Map the two hostnames to 192.168.29.20 in the client hosts file.
6. Open the four URLs. Save research through the admin form, restart only `deployment/app-research`, and compare the content before and after restart. Check the legacy service on NodePort 30081 again.

The static volume is pinned to `k8s-worker1` and retained when the claim is removed. The recovery test covers Pod replacement on that worker.

### Kubernetes commands

Run these commands from the repository root using the lab's Kubernetes context. Create a mode 0600 environment file outside the repository with `ADMIN_USER` and `ADMIN_PASSWORD`, then replace `/secure/research-admin.env` with its location. Image credentials, if needed by the workers, should be configured before deploying the apps.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n student-web create secret generic research-admin \
  --from-env-file=/secure/research-admin.env
kubectl apply -f k8s/research-pv.yaml -f k8s/research-pvc.yaml
kubectl apply -f k8s/about.yaml -f k8s/api.yaml -f k8s/research.yaml
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik --version 42.4.1 \
  --namespace traefik --create-namespace --skip-crds --wait \
  -f k8s/traefik-values.yaml
kubectl apply -f k8s/ingress.yaml
kubectl -n student-web get deployments,pods,services,ingress,pvc
kubectl -n student-web describe ingress student-ingress
kubectl -n student-web describe pvc research-data
```

Add the two entries from [config/linux-hosts.example](config/linux-hosts.example) to the Linux client's `/etc/hosts`, preserving its existing entries. Verify resolution with `getent hosts www.id-539.com admin.id-539.com`.

The lab uses HTTP on the private VMware network. Screenshots with student data belong in the assignment evidence, separate from the public source repository.
