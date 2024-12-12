# Change from python:3.12-slim to python:3.11-slim
FROM python:3.11-slim


# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libaio-dev \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port for the bot (optional if you want to run the bot in webhooks mode, but for polling this is not necessary)
EXPOSE 80

# Command to run the bot
CMD ["python", "bot.py"]
