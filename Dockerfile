FROM python:3.12-slim

# Install build dependencies for aiohttp and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    python3-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install your dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
