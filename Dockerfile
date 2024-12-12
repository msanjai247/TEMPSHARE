# Use an official Python image as the base image
FROM python:3.12-slim

# Install system dependencies for building packages with C extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libaio-dev \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your Python files into the container
COPY . /app

# Install the required Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Command to run the bot
CMD ["python", "bot.py"]
