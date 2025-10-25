# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .

# Install Tesseract dependencies FIRST
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Image - Run the application
FROM python:3.11-slim

WORKDIR /app

# Copy Tesseract from builder
COPY --from=builder /usr/bin/tesseract /usr/bin/tesseract
COPY --from=builder /usr/share/tesseract-ocr /usr/share/tesseract-ocr

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Command to run the worker
CMD ["python", "worker.py"]