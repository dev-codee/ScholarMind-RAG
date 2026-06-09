FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install build dependencies for libraries like chromadb
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency file
COPY pyproject.toml .

# Install Python dependencies using pip
RUN pip install --no-cache-dir .

# Copy the rest of the application files
COPY . .

# Railway automatically detects and binds to the PORT environment variable
# We expose both for local testing
EXPOSE 8000
EXPOSE 8501

# Run the app
CMD ["python", "run.py"]
