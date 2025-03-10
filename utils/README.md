# Build container

Change the `model_repo` at `download_model.py` as desired. Then run:
```bash
export HF_TOKEN=XXX
podman build --build-arg HF_TOKEN=$HF_TOKEN . -t modelcar-example:latest --platform linux/amd64
```

# Push container

```bash
podman push modelcar-example:latest quay.io/<your-registry>/modelcar-example:latest
```
