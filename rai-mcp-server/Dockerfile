FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY RAI_Validation_Dataset.csv .

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]
