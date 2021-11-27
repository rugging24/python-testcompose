from typing import Any, Dict
from uuid import uuid4
from fastapi import FastAPI
import sqlalchemy
import os
import json
import uvicorn
from confluent_kafka import Producer, Consumer, KafkaError

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
    response: Dict[str, Any] =dict()
    try:
        db_url = os.getenv("DB_URL")

        e = sqlalchemy.create_engine(
            f"postgresql+psycopg2://{db_url}"
        )
        result = e.execute("select version()")
        version = None
        if result:
            for row in result:
                if not version:
                    version = row[0]
        if version:
            response.update({"version": version})
    except Exception as exc:
        print(exc)
        response = {"Error": "Internal Server Error"}
    return response

def kafka_producer(data: Dict[str, Any]):
    print(data)
    try:
        producer = Producer({
            "bootstrap.servers": f"{os.getenv('KAFKA_BOOTSTRAP_SERVERS')}",
            "debug": "all",
            "socket.timeout.ms": 60
        })
        producer.poll(0)
        producer.produce(f"{os.getenv('KAFKA_TOPIC')}", json.dumps(data).encode('utf-8'))

        producer.flush()
        return {"status": "success"}
    except:
        return {"status": "failed"}

def kafka_consumer(data: Dict[str, Any]):
    version = dict()
    try:
        c = Consumer({
            "bootstrap.servers": f"{os.getenv('KAFKA_BOOTSTRAP_SERVERS')}",
            "group.id": data.get("group_id") or uuid4().hex,
            "auto.offset.reset": f"{os.getenv('KAFKA_OFFSET_RESET')}",
            "debug": "broker, topic, protocol"
        })
        c.subscribe([f"{os.getenv('KAFKA_TOPIC')}"])
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                break
            else:
                version = json.loads(json.loads(msg.value().decode('utf-8')))
                break
        c.close()
    except:
        return version
    return version
      
if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0') # type: ignore