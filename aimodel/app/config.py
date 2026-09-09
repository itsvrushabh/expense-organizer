import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL_MODEL = BASE_DIR / "models" / "qwen2.5-0.5b-instruct-q4_k_m.gguf"
DEFAULT_DOCKER_MODEL = Path("/app/models/qwen2.5-0.5b-instruct-q4_k_m.gguf")

if os.path.exists(str(DEFAULT_DOCKER_MODEL)):
    DEFAULT_MODEL = str(DEFAULT_DOCKER_MODEL)
else:
    DEFAULT_MODEL = str(DEFAULT_LOCAL_MODEL)

MODEL_PATH = os.getenv("MODEL_PATH", DEFAULT_MODEL)

# GPU configuration: -1 offloads all layers to NVIDIA GPU via CUDA
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "-1"))
N_CTX = int(os.getenv("N_CTX", "2048"))

# Server config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))
