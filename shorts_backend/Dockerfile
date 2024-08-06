# Use a Python base image
FROM python:3.9-slim

# Create a working directory within the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your Flask application code
COPY ./ .

# Expose the port where your Flask app runs (usually 5000)
EXPOSE 5050

CMD ["python", "app.py"]

