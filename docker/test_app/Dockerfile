FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils && \
    && apt-get install -y librdkafka-dev && \
    pip install --upgrade pip sqlalchemy psycopg2-binary fastapi "uvicorn[standard]" confluent-kafka

COPY docker/test_app/app.py /app/app.py

EXPOSE 8000

CMD python /app/app.py
