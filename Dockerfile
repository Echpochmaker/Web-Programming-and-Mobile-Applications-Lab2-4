FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Команда будет переопределена в docker-compose, но оставим на всякий случай
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4200"]