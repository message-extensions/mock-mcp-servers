FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server-multi-auth.py .
COPY .env .

# Copy document repository and metadata
COPY metadata.json .
COPY docs/ ./docs/

# Expose port (auth server runs on port 3001)
EXPOSE 3001

# Run the server
CMD ["python", "server-multi-auth.py"]