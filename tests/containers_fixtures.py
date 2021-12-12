import pytest


@pytest.fixture(scope="module")
def db_and_app_containers():
    return {
        "services": [
            {
                "name": "database",
                "image": "postgres:13",
                "auto_remove": True,
                "command": "",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "postgres",
                    "POSTGRES_PASSWORD": "password",
                },
                "exposed_ports": ["5432"],
                "log_wait_parameters": {
                    "log_line_regex": ".*database system is ready to accept connections.*",
                    "wait_timeout": 30,
                    "poll_interval": 2,
                },
            },
            {
                "name": "application",
                "image": "test-docker-python",
                "auto_remove": True,
                "command": "",
                "environment": {
                    "DB_URL": "${database.postgres_user}:${database.postgres_password}@${database.docker_python_internal_host}:5432/${database.postgres_db}"
                },
                "exposed_ports": ["8000"],
                "log_wait_parameters": {
                    "log_line_regex": ".*Application startup complete.*",
                    "wait_timeout": 60,
                    "poll_interval": 2,
                },
                "http_wait_parameters": {
                    "http_port": 8000,
                    "response_status_code": 200,
                    "end_point": "/ping",
                    "startup_delay_time": 30,
                },
                "depends_on": ["database"],
            },
        ]
    }


@pytest.fixture(scope="module")
def broker_app_and_db_containers():
    return {
        "network": {"name": "test_network", "auto_create": False, "use_random_network": True},
        "services": [
            {
                "name": "database",
                "image": "postgres:13",
                "auto_remove": True,
                "command": "",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "postgres",
                    "POSTGRES_PASSWORD": "password",
                },
                "exposed_ports": ["5432"],
                "log_wait_parameters": {
                    "log_line_regex": ".*database system is ready to accept connections.*",
                    "wait_timeout": 30,
                    "poll_interval": 2,
                },
            },
            {
                "name": "application",
                "image": "python:3.9",
                "auto_remove": True,
                "command": "/bin/bash -x /run_app.sh",
                "volumes": [
                    {
                        "host": "docker-test-files/run_app.sh",
                        "container": "/run_app.sh",
                        "mode": "ro",
                        "source": "local",
                    },
                    {
                        "host": "docker-test-files/app.py",
                        "container": "/app.py",
                        "mode": "ro",
                        "source": "local",
                    },
                ],
                "environment": {
                    "DB_URL": "${database.postgres_user}:${database.postgres_password}@${database.docker_python_internal_host}:5432/${database.postgres_db}",
                    "KAFKA_BOOTSTRAP_SERVERS": "${kafka.docker_python_internal_host}:29092",
                    "KAFKA_OFFSET_RESET": "earliest",
                    "KAFKA_TOPIC": "test_kafka_topic",
                },
                "exposed_ports": ["8000"],
                "http_wait_parameters": {
                    "http_port": 8000,
                    "response_status_code": 200,
                    "end_point": "/ping",
                    "startup_delay_time": 30,
                },
                "depends_on": ["database", "kafka"],
            },
            {
                "name": "zookeeper",
                "image": "confluentinc/cp-zookeeper:6.2.1",
                "auto_remove": True,
                "exposed_ports": ["2181"],
                "environment": {"ZOOKEEPER_CLIENT_PORT": "2181", "ZOOKEEPER_TICK_TIME": 2000},
                "log_wait_parameters": {
                    "log_line_regex": ".*Started AdminServer on address.*",
                    "wait_timeout": 60,
                    "poll_interval": 2,
                },
            },
            {
                "name": "kafka",
                "image": "confluentinc/cp-kafka:6.2.1",
                "auto_remove": True,
                "command": "",
                "exposed_ports": ["9092"],
                "log_wait_parameters": {
                    "log_line_regex": ".*Ready to serve as the new controller.*",
                    "wait_timeout": 60,
                    "poll_interval": 2,
                },
                "environment": {
                    "KAFKA_BROKER_ID": 1,
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
                    "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
                    "KAFKA_ZOOKEEPER_CONNECT": "${zookeeper.docker_python_internal_host}:${zookeeper.zookeeper_client_port}",
                    "KAFKA_AUTO_CREATE_TOPICS_ENABLE": 'true',
                    "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://${self.hostname}:29092,CONNECTIONS_FROM_HOST://localhost:${self.hostport_9092}",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,CONNECTIONS_FROM_HOST:PLAINTEXT",
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:29092, CONNECTIONS_FROM_HOST://0.0.0.0:9092",
                    "KAFKA_BROKER_ID": 0,
                },
                "depends_on": ["zookeeper"],
            },
        ],
    }
