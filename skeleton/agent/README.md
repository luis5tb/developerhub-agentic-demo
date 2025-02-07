## Limitations

For now I have to use my own fork of llama-stack to enable granite models and changing microdnf by dnf. Also to import an unmerged fix for vllm + chatcompletion responses

- repo: https://github.com/luis5tb/llama-stack/tree/test-vllm

## Manual steps

1. Clone the repo

```
git clone git@github.com:luis5tb/llama-stack.git
cd llama-stack
git checkout test-vllm
```

2. create virtual env and install llama-stack
```
python -m venv stack
source stack/bin/activate
pip install .
```

3. create base build file
```
cat > vllm-llama-stack-build.yaml << "EOF"
version: '2'
distribution_spec:
  description: Use (an external) vLLM server for running LLM inference
  providers:
    inference:
    - remote::vllm
    vector_io:
    - inline::faiss
    - remote::chromadb
    - remote::pgvector
    safety:
    - inline::llama-guard
    agents:
    - inline::meta-reference
    eval:
    - inline::meta-reference
    datasetio:
    - remote::huggingface
    - inline::localfs
    scoring:
    - inline::basic
    - inline::llm-as-judge
    - inline::braintrust
    telemetry:
    - inline::meta-reference
    tool_runtime:
    - remote::brave-search
    - remote::tavily-search
    - inline::code-interpreter
    - inline::rag-runtime
    - remote::model-context-protocol
  container_image: registry.access.redhat.com/ubi9
image_type: container
EOF
```

4.  Build the llama server container
```
export CONTAINER_BINARY=podman
export LLAMA_STACK_DIR="."
export USE_COPY_NOT_MOUNT="true"
llama stack build --config vllm-llama-stack-build.yaml --image-type container --image-name distribution-remote-vllm
```

5.  Test the llama server container
```
export VLLM_URL=your-vllm-endpoint
export INFERENCE_MODEL=granite-3-8b-instruct
export LLAMA_STACK_PORT=5000
export VLLM_API_TOKEN=your-key

podman run --security-opt label=disable -it --network host \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT  \
  -v ~/.llama/distributions/remote-vllm/remote-vllm-run.yaml:/app/config.yaml \
  --env LLAMA_STACK_PORT=$LLAMA_STACK_PORT \
  --env VLLM_API_TOKEN=$VLLM_API_TOKEN \
  --env INFERENCE_MODEL=$INFERENCE_MODEL \
  --env VLLM_URL=$VLLM_URL \
  --entrypoint='["python", "-m", "llama_stack.distribution.server.server", "--yaml-config", "/app/config.yaml"]' localhost/distribution-remote-vllm:dev
```