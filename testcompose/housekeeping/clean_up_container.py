import socket
from typing import Any, Dict, List
from uuid import uuid4

from testcompose.containers.container_network import ContainerNetwork
from testcompose.containers.generic_container import GenericContainer
from testcompose.log_setup import stream_logger
from testcompose.models.bootstrap.container_service import ContainerService

logger = stream_logger(__name__)


class Housekeeping:
    """description"""

    @staticmethod
    def cleanup_parameters() -> Dict[str, Any]:
        return {
            "name": f"ryuk_container_{uuid4().hex}",
            "image": "docker.io/testcontainers/ryuk",
            "auto_remove": True,
            "command": "",
            "exposed_ports": ["8080"],
            "environment": {
                "RYUK_PORT": "8080",
                "RYUK_CONNECTION_TIMEOUT": 120,
            },
            "volumes": [
                {"host": "/var/run/docker.sock", "container": "/var/run/docker.sock", "mode": "ro"},  # noqa: E501
            ],
            "log_wait_parameters": {
                "log_line_regex": ".*Started!.*",
                "wait_timeout": 30.0,
                "poll_interval": 1,
            },
        }

    @staticmethod
    def start_ryuk_container(docker_client) -> GenericContainer:
        network_name: str = "bridge"
        parameter = Housekeeping.cleanup_parameters()
        ryuk_container: ContainerService = ContainerService(**parameter)
        generic_container: GenericContainer = GenericContainer()
        generic_container.container_network = ContainerNetwork(docker_client, network_name)  # noqa: E501
        generic_container.container_label = str(parameter.get("name"))
        generic_container.with_service(ryuk_container, dict(), network_name)
        generic_container.container = generic_container.start(docker_client=docker_client)  # noqa: E501
        generic_container.check_container_health(docker_client=docker_client)
        return generic_container

    @staticmethod
    def perform_housekeeping(docker_client, labels: List[str]):
        if labels:
            container: GenericContainer = Housekeeping.start_ryuk_container(docker_client)  # noqa: E501
            TCP_IP = container.get_container_host_ip()
            TCP_PORT = int(str(container.get_exposed_port(port="8080")))
            for label in labels:
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.connect((TCP_IP, TCP_PORT))
                _socket.send(bytes(f"label={label}", encoding="utf-8"))
                data = _socket.recv(0)
                logger.info(f"Received: {str(data)} From RYUK")
                _socket.close()
