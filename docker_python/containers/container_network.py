from typing import Dict, List, Optional
from docker.models.networks import Network
from docker.client import DockerClient

class ContainerNetwork:
    def __init__(self, docker_client: DockerClient, network_name) -> None:
        self._docker_client = docker_client
        self.get_defined_network(network_name)

    @property
    def container_network(self) -> Network:
        return self._container_network

    @container_network.setter
    def container_network(self, network: Network) -> None:
        self._container_network = network
    
    @property
    def network_name(self) -> Optional[str]:
        return self.container_network.name

    def get_defined_network(self, network_name: str, auto_create_network: bool=False):
        try:
            _networks: List[Network] = self._docker_client.networks.list(
                names=[network_name]
            ) # type: ignore
        except:
            _networks = list()
        if _networks:
            self.container_network = _networks[0]
        elif not _networks and auto_create_network:
            self.container_network = self._create_group_network(network_name)
        else:
            raise AttributeError
        
    @property
    def container_network_id(self) -> Optional[str]:
        return self.container_network.short_id
    
    def remove_network(self):
        self.container_network.remove()

    def _create_group_network(self, network_name: str, label: Dict[str, str]=dict())  -> Network:
        return self._docker_client.networks.create( # type: ignore
            name=network_name,
            driver="bridge",
            check_duplicate=True,
            internal=False,
            labels=label,
            enable_ipv6=False,
            attachable=True,
            scope="local"
        )