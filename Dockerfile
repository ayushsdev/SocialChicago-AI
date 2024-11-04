FROM python:3.12.6

# Install system dependencies including poppler-utils
RUN apt-get update && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=8000
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
# Start the application
CMD ["gunicorn", "-b", ":8000", "api.app:app"]