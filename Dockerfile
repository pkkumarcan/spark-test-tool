FROM nvidia/cuda:12.6.2-base-ubuntu24.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-dev \
    nvidia-utils-565 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    git \
    curl \
    && ln -sf /usr/bin/python3.12 /usr/bin/python \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application source only — do NOT copy .env (secrets stay on host)
COPY ./app ./app

# Create non-root user and set ownership
RUN useradd -m -u 1001 spark && chown -R spark:spark /app
USER spark

EXPOSE 5050

# Health check so Docker knows if the app is actually healthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5050"]
