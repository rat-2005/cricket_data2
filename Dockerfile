# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces require the app to run on port 7860 and 
# it needs permission to run as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

# Command to run the Flask app using Gunicorn on port 7860 with a 5 minute timeout and 4 threads
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "300", "--threads", "4", "app:app"]
