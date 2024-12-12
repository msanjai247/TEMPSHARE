# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install the Python bindings for libtorrent (precompiled wheels)
RUN pip install python-libtorrent

# Copy the bot code and requirements into the container
COPY . /app

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default port (required by Telegram Bot API)
EXPOSE 80

# Run the bot with unbuffered output for better logging and debugging
CMD ["python", "-u", "bot.py"]
