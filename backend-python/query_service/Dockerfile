# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app

# Install CPU-only torch FIRST
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy the service's requirements file (from the correct path)
COPY query_service/requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM python:3.11-slim
WORKDIR /app

# THIS IS THE FIX
# Force Python to look in /app BEFORE site-packages
ENV PYTHONPATH /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your SHARED code
COPY campusbot_common/ /app/campusbot_common/

# Copy ONLY the service's application code
COPY query_service/ /app/

# Run the application
EXPOSE 8000
CMD ["uvicorn", "routers.main:app", "--host", "0.0.0.0", "--port", "8000"]