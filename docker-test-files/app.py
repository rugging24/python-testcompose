from typing import Any, Dict
from fastapi import FastAPI  # type: ignore
import os
import uvicorn  # type: ignore
from kafka import KafkaProducer, KafkaConsumer  # type: ignore
import json
import psycopg2


app = FastAPI(debug=True)


@app.get("/ping")
def check_service_health():
    return {"status": "pong"}


@app.post("/version/produce")
def store_data_in_kafka(data: Dict[str, Any]):
    return kafka_producer(data=data)


@app.post("/version/consume")
def fetch_data_in_kafka(data: Dict[str, Any]):
    return kafka_consumer(data=data)


@app.get("/version")
def read_version():
    return connect_to_db()


def connect_to_db() -> Dict[str, Any]:
    response: Dict[str, Any] = dict()
    try:
        db_url = os.getenv("DB_URL")
        e = psycopg2.connect(db_url)
        cursor = e.cursor()
        cursor.execute("select version()")
        result = cursor.fetchone()
        version = None
        if result:
            for row in result:
                if not version:
                    version = row
        if version:
            response.update({"version": version})
    except Exception as exc:
        print(exc)
        response = {"Error": "Internal Server Error"}
    return response


def kafka_producer(data: Dict[str, Any]):
    try:
        producer = KafkaProducer(bootstrap_servers=[f"{os.getenv('KAFKA_BOOTSTRAP_SERVERS')}"])
        producer.send(f"{os.getenv('KAFKA_TOPIC')}", json.dumps(data).encode("utf-8"))
        producer.flush()
        producer.close()
        return {"status": "success"}
    except Exception:
        return {"status": "failed"}


def kafka_consumer(data: Dict[str, Any]):
    version = dict()
    try:
        consumer = KafkaConsumer(
            f"{os.getenv('KAFKA_TOPIC')}",
            bootstrap_servers=[f"{os.getenv('KAFKA_BOOTSTRAP_SERVERS')}"],
            group_id=data.get("group_id"),
            auto_offset_reset='earliest',
        )
        for msg in consumer:
            if msg.value:
                version = json.loads((msg.value).decode("utf-8"))
            if version:
                break
        consumer.close()
    except Exception:
        return version
    return version


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")  # type: ignore
