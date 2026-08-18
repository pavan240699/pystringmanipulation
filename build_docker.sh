#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- CONFIGURATION ---
IMAGE_NAME="flask-text-processor"
TAG="latest"

echo "=========================================="
echo "🚀 Starting Docker Setup and Build Process"
echo "=========================================="

# 1. Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "📄 Creating requirements.txt..."
    cat << 'EOF' > requirements.txt
Flask==3.0.3
flasgger==0.9.7.1
tiktoken==0.7.0
Werkzeug==3.0.3
EOF
fi

# 2. Create .dockerignore to keep the image lightweight
echo "🙈 Creating .dockerignore..."
cat << 'EOF' > .dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.venv
env/
venv/
.git
.gitignore
Dockerfile
setup_and_build.sh
EOF

# 3. Create the optimized Dockerfile
echo "🐳 Creating Dockerfile..."
cat << 'EOF' > Dockerfile
# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a local directory to copy over easily
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Copy installed dependencies from the builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code
COPY . .

# Expose the API port
EXPOSE 5000

# Run the application using Gunicorn for production safety
# (Falls back to python app.py if you haven't switched to a production WSGI server yet)
CMD ["python", "app.py"]
EOF

# 4. Build the Docker image
echo "📦 Building Docker image: ${IMAGE_NAME}:${TAG}..."
docker build -t "${IMAGE_NAME}:${TAG}" .

echo "=========================================="
echo "✅ Success! Image built successfully."
echo "👉 To run your container, use:"
echo "   docker run -p 5000:5000 -e API_SECRET_KEY=your_key_here ${IMAGE_NAME}:${TAG}"
echo "=========================================="
