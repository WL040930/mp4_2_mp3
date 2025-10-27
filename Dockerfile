FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies required by moviepy (ffmpeg) and clean up cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
        "flask>=3.0.2" \
        "moviepy>=2.2.1" \
        "openai>=2.6.0" \
        "requests>=2.32.5" \
        "gunicorn>=22.0.0"

# Copy the application source code.
COPY src ./src

# Make the source importable and run the app with Gunicorn.
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["gunicorn", "--chdir", "/app/src", "--bind", "0.0.0.0:8000", "web_app:app"]
