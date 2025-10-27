# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app

# Install CPU-only torch FIRST to prevent build hang
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends\
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \ 
    libsm6 \       
    libxrender1 \  
    libxext6 \
    poppler-utils \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Copy the worker's requirements file (from the correct path)
COPY ingestion_worker/requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM python:3.11-slim
WORKDIR /app

# THIS IS THE FIX
# Force Python to look in /app BEFORE site-packages
ENV PYTHONPATH /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    libsm6 \       
    libxrender1 \  
    libxext6 \
    poppler-utils \
    default-jre-headless \
    # Add libsm6, libxrender1, libxext6 if libgl1 alone isn't enough
    && rm -rf /var/lib/apt/lists/*

# Copy Tesseract
COPY --from=builder /usr/bin/tesseract /usr/bin/tesseract
COPY --from=builder /usr/share/tesseract-ocr /usr/share/tesseract-ocr

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your SHARED code
COPY campusbot_common/ /app/campusbot_common/

# Copy ONLY the worker's application code
COPY ingestion_worker/ /app/

# Run the worker
CMD ["python", "worker.py"]