import json
import re
from unittest import mock
import pytest

from testcompose.configs.parse_config import TestConfigParser


@pytest.fixture(scope="module")
def db_and_app_containers():
    return {
        "services": [
            {
                "name": "database",
                "image": "postgres:13",
                "command": "",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "postgres",
                    "POSTGRES_PASSWORD": "password",
                },
                "exposed_ports": [5432],
                "log_wait_parameters": {
                    "log_line_regex": ".*database system is ready to accept connections.*",
                    "wait_timeout_ms": 30000,
                    "poll_interval_ms": 2000,
                },
            },
            {
                "name": "application",
                "image": "python:3.9",
                "command": "/bin/bash -x /run_app.sh",
                "environment": {
                    "DB_URL": "${database.postgres_user}:${database.postgres_password}@${database.container_hostname}:5432/${database.postgres_db}"
                },
                "volumes": [
                    {
                        "host": "docker-test-files/run_app.sh",
                        "container": "/run_app.sh",
                        "mode": "ro",
                        "source": "filesystem",
                    },
                    {
                        "host": "docker-test-files/app.py",
                        "container": "/app.py",
                        "mode": "ro",
                        "source": "filesystem",
                    },
                ],
                "exposed_ports": [8000],
                "log_wait_parameters": {
                    "log_line_regex": ".*Application startup complete.*",
                    "wait_timeout_ms": 45000,
                    "poll_interval_ms": 2000,
                },
                "http_wait_parameters": {
                    "http_port": 8000,
                    "response_status_code": 200,
                    "end_point": "/ping",
                    "startup_delay_time_ms": 30000,
                    "use_https": False,
                },
                "depends_on": ["database"],
            },
        ]
    }


@pytest.fixture(scope="module")
def broker_app_and_db_containers():
    return {
        "services": [
            {
                "name": "database",
                "image": "postgres:13",
                "command": "",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "postgres",
                    "POSTGRES_PASSWORD": "password",
                },
                "exposed_ports": ["5432"],
                "log_wait_parameters": {
                    "log_line_regex": ".*database system is ready to accept connections.*",
                    "wait_timeout_ms": 30000,
                    "poll_interval_ms": 2000,
                },
            },
            {
                "name": "application",
                "image": "python:3.9",
                "command": "/bin/bash -x /run_app.sh",
                "volumes": [
                    {
                        "host": "docker-test-files/run_app.sh",
                        "container": "/run_app.sh",
                        "mode": "ro",
                        "source": "filesystem",
                    },
                    {
                        "host": "docker-test-files/app.py",
                        "container": "/app.py",
                        "mode": "ro",
                        "source": "filesystem",
                    },
                ],
                "environment": {
                    "DB_URL": "${database.postgres_user}:${database.postgres_password}@${database.container_hostname}:5432/${database.postgres_db}",
                    "KAFKA_BOOTSTRAP_SERVERS": "${kafka.container_hostname}:29092",
                    "KAFKA_OFFSET_RESET": "earliest",
                    "KAFKA_TOPIC": "test_kafka_topic",
                },
                "exposed_ports": ["8000"],
                "http_wait_parameters": {
                    "http_port": 8000,
                    "response_status_code": 200,
                    "end_point": "/ping",
                    "startup_delay_time_ms": 30000,
                },
                "log_wait_parameters": {
                    "log_line_regex": ".*Application startup complete.*",
                    "wait_timeout_ms": 45000,
                    "poll_interval_ms": 2000,
                },
                "depends_on": ["database", "kafka"],
            },
            {
                "name": "zookeeper",
                "image": "confluentinc/cp-zookeeper:6.2.1",
                "exposed_ports": ["2181"],
                "environment": {"ZOOKEEPER_CLIENT_PORT": "2181", "ZOOKEEPER_TICK_TIME": 2000},
                "log_wait_parameters": {
                    "log_line_regex": ".*Started AdminServer on address.*",
                    "wait_timeout_ms": 60000,
                    "poll_interval_ms": 2000,
                },
            },
            {
                "name": "kafka",
                "image": "confluentinc/cp-kafka:6.2.1",
                "command": "",
                "exposed_ports": ["9092"],
                "log_wait_parameters": {
                    "log_line_regex": ".*Ready to serve as the new controller.*",
                    "wait_timeout_ms": 60000,
                    "poll_interval_ms": 2000,
                },
                "environment": {
                    "KAFKA_BROKER_ID": 1,
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
                    "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
                    "KAFKA_ZOOKEEPER_CONNECT": "${zookeeper.container_hostname}:${zookeeper.zookeeper_client_port}",
                    "KAFKA_AUTO_CREATE_TOPICS_ENABLE": 'true',
                    "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://${self.container_hostname}:29092,CONNECTIONS_FROM_HOST://${self.container_host_address}:${self.external_port_9092}",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,CONNECTIONS_FROM_HOST:PLAINTEXT",
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:29092, CONNECTIONS_FROM_HOST://0.0.0.0:9092",
                    "KAFKA_BROKER_ID": 0,
                },
                "depends_on": ["zookeeper"],
            },
        ],
    }


def config_parser_helper(json_config):
    config_services = None
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(json_config))):
        with open('some_file_name') as f2:
            config_services = TestConfigParser.parse_config(file_name=f2.name)
    return config_services


@pytest.fixture(scope='module')
def db_and_app_containers_config_services(db_and_app_containers):
    return config_parser_helper(db_and_app_containers)


@pytest.fixture(scope='module')
def broker_app_and_db_containers_config_services(broker_app_and_db_containers):
    return config_parser_helper(broker_app_and_db_containers)
