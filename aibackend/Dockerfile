FROM python:3.11-slim-bookworm

WORKDIR /app

# Install build dependencies and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install llama-cpp-python using pre-built CPU wheel for fast container build
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu llama-cpp-python && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8001
ENV MODEL_PATH=/app/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
ENV EXPENSE_API_URL=http://backend:8000

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
