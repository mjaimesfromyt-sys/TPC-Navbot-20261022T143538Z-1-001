# ==============================================================================
# TPC NavBot: Multi-Stage Production Dockerfile
# Talibon Polytechnic College (TPC) Gen AI Capstone Project - Checkpoint 4
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder Stage
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build essentials for C-extensions if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a clean prefix directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Final Minimal Runtime Image
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

# Set secure production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Create a non-root system user for security compliance
RUN groupadd -r tpcuser && useradd -r -g tpcuser -d /app -s /sbin/nologin tpcuser

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code, data, and configurations
COPY --chown=tpcuser:tpcuser src/ ./src/
COPY --chown=tpcuser:tpcuser data/ ./data/
COPY --chown=tpcuser:tpcuser docs/ ./docs/
COPY --chown=tpcuser:tpcuser scripts/ ./scripts/
COPY --chown=tpcuser:tpcuser tests/ ./tests/
COPY --chown=tpcuser:tpcuser app.py cli_chat.py requirements.txt README.md ./
COPY --chown=tpcuser:tpcuser .env.example ./.env.example

# Create directory for ChromaDB vector storage with proper ownership
RUN mkdir -p /app/data/chroma_db && chown -R tpcuser:tpcuser /app

# Switch to non-root user
USER tpcuser

# Expose Streamlit application port
EXPOSE 8501

# Healthcheck to verify service availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)"

# Launch the Streamlit application
ENTRYPOINT ["streamlit", "run", "app.py"]
