#!/bin/bash

apt-get update && apt-get install -y --no-install-recommends apt-utils

pip install --upgrade pip sqlalchemy psycopg2-binary fastapi "uvicorn[standard]" kafka-python

python /app.py
