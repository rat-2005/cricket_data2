# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (including Promtail)
RUN apt-get update && apt-get install -y wget unzip \
    && wget https://github.com/grafana/loki/releases/download/v2.9.2/promtail-linux-amd64.zip -O /tmp/promtail.zip \
    && unzip /tmp/promtail.zip -d /usr/local/bin \
    && rm /tmp/promtail.zip \
    && chmod +x /usr/local/bin/promtail-linux-amd64 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy ONLY requirements first to leverage Docker caching
COPY --chown=user requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the code
COPY --chown=user . .

# Ensure start script is executable
RUN chmod +x start.sh

# Command to run both Promtail and Gunicorn via our script
CMD ["./start.sh"]
