# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Set the python path
ENV PYTHONPATH /app/src

# Create a non-root user and group with a home directory
RUN addgroup --system nonroot && \
    adduser --system --ingroup nonroot --home /home/nonroot nonroot

# Set the HOME environment variable
ENV HOME /home/nonroot

# Create directories for NLTK data and Hugging Face cache and set permissions
RUN mkdir -p /home/nonroot/nltk_data && \
    mkdir -p /home/nonroot/.cache/huggingface && \
    chown -R nonroot:nonroot /home/nonroot

# Set environment variables for NLTK and Hugging Face cache
ENV NLTK_DATA /home/nonroot/nltk_data
ENV HUGGINGFACE_HUB_CACHE /home/nonroot/.cache/huggingface

# Install system dependencies for python-magic, libGL, and libgthread
RUN apt-get update && apt-get install -y libmagic1 libgl1 libglib2.0-0 && ldconfig && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first to prevent massive GPU library downloads
# This is the key step to reduce image size
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy the requirements file and set ownership
COPY --chown=nonroot:nonroot ./requirements.txt /app/src/requirements.txt

# Install any needed packages specified in requirements.txt
# Pip will see that torch is already installed and skip it
RUN pip install --no-cache-dir -r src/requirements.txt

# Download NLTK data non-interactively
RUN python -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng'])"

# Copy the src directory and set ownership
COPY --chown=nonroot:nonroot ./src /app/src

# Switch to the non-root user
USER nonroot
