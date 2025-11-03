FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Streamlit default port
ENV PORT=8501

EXPOSE ${PORT}

# Run Streamlit in headless mode
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "${PORT}", "--server.headless", "true", "--server.enableCORS", "false"]
