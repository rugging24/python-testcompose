from typing import Dict, Optional
from docker.models.networks import Network
from docker.client import DockerClient

class ContainerNetwork:
    def __init__(self, docker_client: DockerClient) -> None:
        self._docker_client = docker_client

    @property
    def container_network(self) -> Network:
        return self._container_network

    @container_network.setter
    def container_network(self, network: Network) -> None:
        self._container_network = network
    
    @property
    def network_name(self) -> Optional[str]:
        return self.container_network.name

    def delete_group_network(self):
        self._docker_client.networks.prune(
            filters=""
        )

    def create_group_network(self, network_name: str, label: Dict[str, str]):
        self.container_network  = self._docker_client.networks.create( # type: ignore
            name=network_name,
            driver="bridge",
            check_duplicate=True,
            internal=False,
            labels=label,
            enable_ipv6=False,
            attachable=True,
            scope="local"
        ) 
    
    def get_container_network_id(self) -> Optional[str]:
        return str(self.container_network.id) if self.container_network.id else None
    
    def add_container_to_network(self, container_id) -> None:
        self.container_network.connect(
            container=container_id
        )