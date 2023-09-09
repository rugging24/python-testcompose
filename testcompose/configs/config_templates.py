from typing import Any, Dict


def simple_app_or_db() -> Dict[str, Any]:
    return {
        "name": "service-name",
        "image": "some-valid-image-name",
        "auto_remove": True,
        "command": "",
        "exposed_ports": ["1031"],
        "environment": {
            "ENV_VARIABLE_1": "VALUE_1",
            "ENV_VARIABLE_2": "VALUE_2",
            "ENV_VARIABLE_N": "...VALUE_N",
        },
        "volumes": [
            {"host": "/some-valid-location-on-host", "container": "/data", "mode": "rw"},  # noqa: E501
            {
                "host": "/another-valid-location-on-host",
                "container": "/data2",
                "mode": "ro",  # This is one of rw|ro
            },
        ],
        "log_wait_parameters": {
            "log_line_regex": ".*Some regex to check for in the container log.*",
            "wait_timeout": 30.0,
            "poll_interval": 1,
        },
        "http_wait_parameters": {
            "http_port": "8080",
            "response_status_code": 200,
            "end_point": "/ping",
            "startup_delay_time": 20,
        },
        "depends_on": [],
    }


def simple_broker() -> Dict[str, Any]:
    return {
        "services": [
            {
                "name": "zookeeper",
                "image": "confluentinc/cp-zookeeper:6.2.1",
                "exposed_ports": ["2181"],
                "environment": {"ZOOKEEPER_CLIENT_PORT": "2181", "ZOOKEEPER_TICK_TIME": 2000},  # noqa: E501
                "log_wait_parameters": {
                    "log_line_regex": ".*Started AdminServer on address.*",
                    "wait_timeout_ms": 60000,
                    "poll_interval_ms": 2000,
                },
            },
            {
                "name": "broker",
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
                    "KAFKA_ZOOKEEPER_CONNECT": "${zookeeper.container_hostname}:${zookeeper.zookeeper_client_port}",  # noqa: E501
                    "KAFKA_AUTO_CREATE_TOPICS_ENABLE": 'true',
                    "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://${self.container_hostname}:29092,CONNECTIONS_FROM_HOST://${self.container_host_address}:${self.external_port_9092}",  # noqa: E501
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,CONNECTIONS_FROM_HOST:PLAINTEXT",  # noqa: E501
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:29092, CONNECTIONS_FROM_HOST://0.0.0.0:9092",
                },
                "depends_on": ["zookeeper"],
            },
        ],
    }
