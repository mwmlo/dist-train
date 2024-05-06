# dist-train

A distributed system for training ML models.

## Setup

Training takes place in a Kubernetes cluster `distml`.

```bash
docker build -f Dockerfile -t dist-train:v0.1 .
k3d image import dist-train:v0.1 --cluster distml
```

Switch to "kubeflow" namespace and create persistent storage volume:

```bash
kubectl config set-context --current --namespace=kubeflow
kubectl create -f multi-worker-pvc.yaml
```

## Submit training job

Create a TensorFlow job:

```bash
kubectl create -f multi-worker-tfjob.yaml
```

To resubmit the job:

```bash
kubectl delete tfjob --all
docker build -f Dockerfile -t dist-train:v0.1 .
k3d image import dist-train:v0.1 --cluster distml
kubectl create -f multi-worker-tfjob.yaml
```

## Workflow

```bash
kubectl create -f workflow.yaml
```

### Debugging

```bash
kubectl create -f access-model.yaml 
kubectl exec --stdin --tty access-model -- ls /trained_model
# Manually copy
# kubectl cp trained_model access-model:/pv/trained_model -c model-storage
```
