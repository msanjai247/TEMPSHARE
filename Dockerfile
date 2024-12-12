# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (curl, required for file uploads)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install necessary Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code into the container
COPY . /app

# Expose the default port (if needed for Koyeb)
EXPOSE 80

# Run the bot
CMD ["python", "-u", "bot.py"]
