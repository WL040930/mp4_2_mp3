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
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
        gunicorn>=22.0.0

# Copy the application source code.
COPY src ./src

# Make the source importable and run the app with Gunicorn.
ENV PYTHONPATH=/app/src
EXPOSE 7680

CMD ["gunicorn", "--bind", "0.0.0.0:7680", "web_app:app"]
