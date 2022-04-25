import json
from requests import get, post
from testcompose.configs.service_config import Config
from testcompose.models.config.config_services import ConfigServices
from testcompose.models.container.running_container import RunningContainer
from testcompose.run_containers import RunContainers
from containers_fixtures import (
    db_and_app_containers,
    broker_app_and_db_containers,
    db_and_app_containers_config_services,
    broker_app_and_db_containers_config_services,
)


def test_db_and_app_containers(db_and_app_containers, db_and_app_containers_config_services):
    config_services: ConfigServices = db_and_app_containers_config_services
    running_config = Config(test_services=config_services)
    assert running_config.ranked_config_services
    with RunContainers(
        config_services=config_services,
        ranked_services=running_config.ranked_config_services,
    ) as runner:
        assert runner
        app_container_srv_name = "application"
        app_service: RunningContainer = runner.running_containers[app_container_srv_name]
        app_env_vars = app_service.config_environment_variables
        mapped_port = app_service.generic_container.get_exposed_port("8000")
        print(app_env_vars)
        app_host = app_service.generic_container.get_container_host_ip()
        assert app_env_vars
        assert mapped_port
        assert app_host
        print(f"http://{app_host}:{int(mapped_port)}/version")
        response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
        print(response)
        assert response
        assert response.status_code == 200
        assert response.text
        assert isinstance(json.loads(response.text), dict)


# def test_broker_app_and_db_containers(broker_app_and_db_containers, broker_app_and_db_containers_config_services) -> None:
#     config_services = broker_app_and_db_containers_config_services
#     running_config = Config(test_services=config_services)
#     assert running_config.ranked_config_services
#     with RunContainers(
#          config_services=config_services,
#         ranked_services=running_config.ranked_config_services
#     ) as runner:
#         assert runner
#         app_container_srv_name = "application"
#         app_service: RunningContainer = runner[app_container_srv_name]
#         app_env_vars = app_service.config_environment_variables
#         mapped_port = app_service.container.get_exposed_port("8000")
#         assert mapped_port
#         app_host = app_service.container.get_container_host_ip()
#         response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
#         assert response
#         assert response.status_code == 200
#         version = response.text
#         assert isinstance(json.loads(version), dict)

#         # produce the version to kafka
#         produce_kafka_msg(runner, app_env_vars, version)

#         # consume the message from kafka
#         headers = {"Content-Type": "application/json"}
#         consume = post(
#             url=f"http://{app_host}:{int(mapped_port)}/version/consume",
#             json=json.loads(json.dumps({"group_id": "testing_kafka"})),
#             headers=headers,
#         )
#         assert consume.status_code == 200
#         assert json.loads(consume.text) == json.loads(version)


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
