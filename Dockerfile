FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết cho WeasyPrint
RUN apt-get update && apt-get install -y \
    python3-pip python3-cffi python3-brotli libpango-1.0-0 \
    libharfbuzz0b libpangoft2-1.0-0 libpangocairo-1.0-0 \
    fontconfig fonts-dejavu-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Chạy ứng dụng với uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
