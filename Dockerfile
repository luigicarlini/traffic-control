# Use minimal, secure Python image
FROM python:3.13-alpine

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY app/ .

# Set environment variables (optional)
ENV FLASK_ENV=production

# Expose Flask port
EXPOSE 5050

# Run the application
CMD ["python", "main.py"]
