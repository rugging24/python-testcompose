FROM python:3.9

WORKDIR /app

RUN pip install --upgrade pip sqlalchemy psycopg2-binary fastapi "uvicorn[standard]" confluent-kafka

COPY docker/test_app/app.py /app/app.py

EXPOSE 8000

CMD python /app/app.py