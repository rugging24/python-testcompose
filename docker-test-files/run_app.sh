#!/bin/bash

apt-get update && apt-get install -y --no-install-recommends apt-utils && \
apt-get install -y librdkafka-dev

pip install --upgrade pip sqlalchemy psycopg2-binary fastapi "uvicorn[standard]"

#confluent-kafka

python /app.py
