# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry or just use requirements.txt
# Using requirements.txt for simplicity here
COPY requirements.txt .

# Install dependencies
# --no-cache-dir is crucial
# We install sentence-transformers first to pre-download models if possible
RUN pip install --no-cache-dir sentence-transformers
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Image - Run the application
FROM python:3.11-slim

WORKDIR /app

# Copy *only* the installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the application
# --host 0.0.0.0 is MANDATORY to be reachable from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]