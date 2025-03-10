import os
from huggingface_hub import snapshot_download, login

# Specify the Hugging Face repository containing the model
model_repo = "meta-llama/Llama-3.2-3B-Instruct"
# model_repo = "meta-llama/Llama-3.1-8B-Instruct"
# model_repo = "ibm-granite/granite-3.2-8b-instruct"

hf_token = os.getenv('HF_TOKEN')
login(token=hf_token)
snapshot_download(
        repo_id=model_repo,
        local_dir="/models",
        allow_patterns=["*.safetensors", "*.json", "*.txt"],
)
