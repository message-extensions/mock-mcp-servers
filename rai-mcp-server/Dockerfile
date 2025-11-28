FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py .
COPY RAI_Validation_Dataset.csv .
COPY resources/ ./resources/

# Expose the port the app runs on
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]
