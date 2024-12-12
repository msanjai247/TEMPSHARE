# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for libtorrent
RUN apt-get update && apt-get install -y \
    libtorrent-rasterbar-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the Python bindings for libtorrent
RUN pip install python-libtorrent

# Copy the bot code and requirements into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default port (required by Telegram Bot API)
EXPOSE 80

# Run the bot with unbuffered output for better logging and debugging
CMD ["python", "-u", "bot.py"]
