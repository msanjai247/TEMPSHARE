# Use an official Python image as the base image
FROM python:3.12-slim

# Install dependencies needed for compiling
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libaio-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application files into the container
COPY . /app

# Install required Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Command to run the application
CMD ["python", "bot.py"]
