# Продакшн-образ. На Linux multiprocessing використовує fork, тож дочірній
# процес оцінювання успадковує вже імпортовані шаблони (Windows-нюанс зі spawn
# тут не діє).
FROM python:3.12-slim

WORKDIR /app

# psycopg[binary] — драйвер Postgres для проду (SQLite лишається для розробки).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.1"

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Порт беремо з $PORT (Render/Fly задають його), інакше 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
