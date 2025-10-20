FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "automacao_cotacoes:app", "-b", "0.0.0.0:5000"]
