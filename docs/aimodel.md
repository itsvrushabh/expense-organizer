# AI Model Server Microservice (`aimodel`) 🤖⚡

`aimodel` is a containerized microservice running on port `8002` that provides **GPU-accelerated LLM Inference** using `llama-cpp-python` and `Qwen2.5-0.5B-Instruct-GGUF`. It runs the model on the GPU (NVIDIA GeForce GTX 1650 Ti) and exposes OpenAI-compatible and text generation APIs. It does not contain application business logic or tool execution logic; all agentic orchestration is handled by `aibackend`.

---

## 1. System Role

```mermaid
flowchart LR
    AIB["aibackend Orchestrator (port 8001)<br/>• Sends tool-calling prompts<br/>• Receives model JSON decisions"]
    
    subgraph AIM["aimodel Container (port 8002)"]
        Server["FastAPI Model Server"]
        GPU["GPU CUDA Offload Engine<br/>NVIDIA GTX 1650 Ti (4GB VRAM)<br/>n_gpu_layers = -1 (All 24 layers)<br/>Model: qwen2.5-0.5b-instruct-q4_k_m.gguf"]
        Server --> GPU
    end

    AIB -->|"POST /v1/chat/completions"| Server
```

---

## 2. GPU Acceleration & Model Configuration

- **Target GPU**: NVIDIA GeForce GTX 1650 Ti (4096 MiB VRAM)
- **Model**: `qwen2.5-0.5b-instruct-q4_k_m.gguf` (~397 MB / 469 MB uncompressed)
- **VRAM Required**: ~450–600 MB (fits safely inside 4 GB VRAM)
- **Offload Parameter**: `N_GPU_LAYERS=-1` (all 24 transformer layers offloaded to GPU via CUDA)
- **Port**: `8002`
- **Device Status**: Reported in `GET /health`:
  ```json
  {
    "status": "healthy",
    "model_file_exists": true,
    "model_loaded": true,
    "model_path": "/app/models/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    "device": "GPU CUDA Offload (n_gpu_layers=-1)"
  }
  ```

### Download Command
```bash
mkdir -p aimodel/models
curl -L \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf" \
  -o aimodel/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

---

## 3. Endpoints

- `GET /`: Service metadata, device info, and endpoints catalog.
- `GET /health`: Health status, model loaded flag, and GPU device info.
- `POST /v1/chat/completions`: OpenAI-compatible chat completion endpoint supporting `messages`, `temperature`, `max_tokens`, and `response_format={"type": "json_object"}`.
- `POST /generate`: Raw text completion endpoint taking `{ "prompt": "...", "temperature": 0.1, "max_tokens": 256 }`.

---

## 4. Running with Docker Compose

```bash
# Start aimodel container
docker-compose up -d aimodel

# View aimodel logs
docker-compose logs -f aimodel
```

### Access Points
- 🤖 **AI Model Service**: `http://localhost:8002`
- 🩺 **Health Check**: `http://localhost:8002/health`
- 📚 **Swagger Docs**: `http://localhost:8002/docs`

---

## 5. Testing

```bash
cd aimodel
pytest tests/ -v
```
All 4 tests verify `/health`, `/v1/chat/completions`, and `/generate` endpoints.
