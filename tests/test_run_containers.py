import json
from typing import Any, Dict
from requests import Response, get, post
from testcompose.configs.service_config import Config
from testcompose.models.bootstrap.container_service import ContainerServices
from testcompose.models.container.running_container import RunningContainer
from testcompose.run_containers import RunContainers
from .containers_fixtures import (
    db_and_app_containers,
    broker_app_and_db_containers,
    db_and_app_containers_config_services,
    broker_app_and_db_containers_config_services,
)
from kafka import KafkaProducer  # type: ignore


def test_db_and_app_containers(db_and_app_containers, db_and_app_containers_config_services):
    config_services: ContainerServices = db_and_app_containers_config_services
    running_config: Config = Config(test_services=config_services)
    assert running_config.ranked_config_services
    with RunContainers(
        config_services=config_services,
        ranked_services=running_config.ranked_config_services,
    ) as runner:
        assert runner
        app_container_srv_name = "application"
        app_service: RunningContainer = runner.running_containers[app_container_srv_name]
        app_env_vars: Dict[str, Any] = app_service.config_environment_variables
        mapped_port = app_service.generic_container.get_exposed_port("8000")
        print(app_env_vars)
        app_host = app_service.generic_container.get_container_host_ip()
        assert app_env_vars
        assert mapped_port
        assert app_host
        response: Response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
        assert response
        assert response.status_code == 200
        assert response.text
        assert isinstance(json.loads(response.text), dict)


def test_broker_app_and_db_containers(
    broker_app_and_db_containers, broker_app_and_db_containers_config_services
) -> None:
    config_services = broker_app_and_db_containers_config_services
    running_config = Config(test_services=config_services)
    assert running_config.ranked_config_services

    with RunContainers(
        config_services=config_services, ranked_services=running_config.ranked_config_services
    ) as runner:
        assert runner
        app_container_srv_name: str = "application"
        assert runner.running_containers

        app_service: RunningContainer = runner.running_containers[app_container_srv_name]
        mapped_port = app_service.generic_container.get_exposed_port("8000")
        assert mapped_port
        app_host = app_service.generic_container.get_container_host_ip()
        response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
        assert response
        assert response.status_code == 200
        version = response.text
        assert isinstance(json.loads(version), dict)

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        # produce the version to kafka
        producer = post(
            url=f"http://{app_host}:{int(mapped_port)}/version/produce",
            json=json.loads(version),
            headers=headers,
        )

        assert producer.status_code == 200
        assert json.loads(producer.text) == {"status": "success"}
        # consume the message from kafka
        consumer = post(
            url=f"http://{app_host}:{int(mapped_port)}/version/consume",
            json={"group_id": "testing_kafka"},
            headers=headers,
            timeout=30.0,
        )
        assert consumer.status_code == 200
        assert json.loads(consumer.text) == json.loads(version)
