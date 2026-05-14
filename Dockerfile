FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scrapling/curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p data

EXPOSE 8501

# start.sh: seeds demo data if DB missing, then launches Streamlit
CMD ["bash", "start.sh"]
