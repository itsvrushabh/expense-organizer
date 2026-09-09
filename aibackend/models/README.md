# AI Models Directory

Place the GGUF model file in this directory before starting the AI microservice.

### Recommended Model
- **Filename**: `qwen2.5-0.5b-instruct-q4_k_m.gguf`
- **Model**: Qwen 2.5 0.5B Instruct (GGUF 4-bit Medium Quantization)
- **Size**: ~397 MB
- **Target Path**: `aibackend/models/qwen2.5-0.5b-instruct-q4_k_m.gguf`

### Download Command
```bash
curl -L \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf" \
  -o aibackend/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

### Fallback / Alternative Model
If you prefer a 1.5B parameter model with higher reasoning capacity (~986 MB):
```bash
curl -L \
  "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf" \
  -o aibackend/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```
*(If using the 1.5B model, update `MODEL_PATH` in `docker-compose.yml` or `.env` accordingly).*
