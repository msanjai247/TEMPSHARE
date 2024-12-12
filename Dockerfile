# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean

# Expose the port that the bot will run on
EXPOSE 8080

# Run the application
CMD ["python", "bot.py"]
