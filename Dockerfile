FROM python:3.10-slim
WORKDIR /app
COPY . /app

# Install dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]