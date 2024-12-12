# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the bot code and requirements
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default port (required by Telegram Bot API)
EXPOSE 80

# Run the bot
CMD ["python", "bot.py"]
