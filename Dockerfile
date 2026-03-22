FROM python:3.11

# Install Tesseract OCR + system libraries needed by numpy/scipy/PIL/sklearn
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Strip Windows CRLF line endings and make executable
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["/bin/bash", "start.sh"]
