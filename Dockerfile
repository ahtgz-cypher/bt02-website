FROM python:3.11-slim

WORKDIR /app

# Cai dat cac thu vien can thiet
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toan bo ma nguon website
COPY . .

# Expose cong 8080
EXPOSE 8080

# Chay ung dung Flask thong qua production WSGI Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
