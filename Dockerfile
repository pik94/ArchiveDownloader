FROM python:3.7-slim

COPY . /app

EXPOSE 8000
WORKDIR /app
VOLUME /app/logs
VOLUME /app/storage

RUN apt update && apt install -y zip && python3 -m pip install -r requirements.txt

ENV DEBUG=-d
ENV HOST=0.0.0.0
ENV PORT=8080
ENV STORAGE_PATH=/app/storage
ENV LOG_FILE=/app/logs/archive.log
ENV CHUNK_SIZE=100
ENV DELAY=0.5

ENTRYPOINT python3 server.py \
    $DEBUG \
    --host $HOST \
    --port $PORT \
    --storage_path $STORAGE_PATH \
    --log_file $LOG_FILE \
    --chunk_size $CHUNK_SIZE \
    --delay $DELAY