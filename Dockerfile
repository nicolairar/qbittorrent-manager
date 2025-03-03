FROM python:3.9-slim

WORKDIR /app

# Installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crea directory per i log e imposta permessi
RUN mkdir -p /var/log && \
    touch /var/log/qbit_queue_manager.log && \
    chmod 777 /var/log/qbit_queue_manager.log

# Copia i file dell'applicazione
COPY queue_manager.py .
COPY .env .

CMD ["python", "-u", "queue_manager.py"]
