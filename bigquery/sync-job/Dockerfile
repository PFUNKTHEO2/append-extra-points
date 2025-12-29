FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the sync script
COPY sync_rankings.py .

# Run the sync
CMD ["python", "sync_rankings.py"]
