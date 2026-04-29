FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папки для логов и данных, чтобы при монтировании volumes не было проблем с правами
RUN mkdir -p logs data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
