import json
from typing import Any, Dict, Tuple
from io import BytesIO
import tarfile
from requests import get, post
from testcompose.configs.service_config import Config
from testcompose.models.config import ITestConfig
from testcompose.run_containers import RunContainers
from containers_fixtures import db_and_app_containers, broker_app_and_db_containers


def test_db_and_app_containers(db_and_app_containers):
    running_config = Config(test_services=ITestConfig(**db_and_app_containers))
    assert running_config.ranked_itest_config_services
    with RunContainers(
        services=running_config.ranked_itest_config_services,
    ) as runner:
        assert runner.containers
        app_container_srv_name = "application"
        app_env_vars = runner.extra_envs[app_container_srv_name]
        mapped_port = app_env_vars.get("DOCKER_PYTHON_MAPPED_PORTS", {}).get("8000")
        print(app_env_vars)
        app_host = app_env_vars.get("DOCKER_PYTHON_EXTERNAL_HOST")
        assert app_env_vars
        assert mapped_port
        assert app_host
        response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
        print(response)
        assert response
        assert response.status_code == 200
        assert response.text
        assert isinstance(json.loads(response.text), dict)


def test_broker_app_and_db_containers(broker_app_and_db_containers) -> None:
    running_config = Config(test_services=ITestConfig(**broker_app_and_db_containers))
    assert running_config.ranked_itest_config_services
    with RunContainers(services=running_config.ranked_itest_config_services) as runner:
        assert runner.containers
        app_container_srv_name = "application"
        app_env_vars = runner.extra_envs[app_container_srv_name]
        app_mapped_port = app_env_vars.get("DOCKER_PYTHON_MAPPED_PORTS", {}).get("8000")
        assert app_mapped_port
        app_host = app_env_vars.get("DOCKER_PYTHON_EXTERNAL_HOST")
        response = get(url=f"http://{app_host}:{int(app_mapped_port)}/version")
        assert response
        assert response.status_code == 200
        version = response.text
        assert isinstance(json.loads(version), dict)

        # produce the version to kafka

        produce_kafka_msg(runner, app_env_vars, version)

        # consume the message from kafka
        headers = {"Content-Type": "application/json"}
        consume = post(
            url=f"http://{app_host}:{int(app_mapped_port)}/version/consume",
            json=json.loads(json.dumps({"group_id": "testing_kafka"})),
            headers=headers,
        )
        assert consume.status_code == 200

        assert json.loads(consume.text) == json.loads(version)


def produce_kafka_msg(runner, app_env_vars, version):
    from kafka import KafkaProducer

    kafka_env_vars = runner.extra_envs["kafka"]
    kafka_mapped_port = kafka_env_vars.get("DOCKER_PYTHON_MAPPED_PORTS", {}).get("9092")
    assert kafka_mapped_port

    producer = KafkaProducer(
        bootstrap_servers=f"{kafka_env_vars.get('DOCKER_PYTHON_EXTERNAL_HOST')}:{kafka_mapped_port}"
    )
    producer.send(
        f"{app_env_vars.get('KAFKA_TOPIC')}", json.dumps(json.dumps(json.loads(version))).encode("utf-8")
    )

    producer.flush()
    producer.close()
