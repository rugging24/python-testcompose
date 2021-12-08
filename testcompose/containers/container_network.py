from typing import Dict, List, Optional
from docker.models.networks import Network
from testcompose.models.network import NetworkConstants
from docker.client import DockerClient


class ContainerNetwork:
    """Network management for running container.This class ensures
    all containers in the same test belong to the same network.
    Contians utility to create and cleanup network.

    Args:
        docker_client (DockerClient): Docker client
        network_name (str): Name of test network
        auto_create_network (bool, optional): Create network if it doesn't exists. Defaults to False.
    """

    def __init__(
        self, docker_client: DockerClient, network_name: str, auto_create_network: bool = False
    ) -> None:
        self._docker_client = docker_client
        self.get_defined_network(network_name, auto_create_network)

    @property
    def container_network(self) -> Network:
        """Network Object

        Returns:
            Network: container network object
        """
        return self._container_network

    @container_network.setter
    def container_network(self, network: Network) -> None:
        self._container_network = network

    @property
    def network_name(self) -> Optional[str]:
        """Network Name

        Returns:
            Optional[str]: Network Name
        """
        return self.container_network.name

    def get_defined_network(self, network_name: str, auto_create_network: bool = False):
        """Identify or create container network

        Args:
            network_name (str): Network name
            auto_create_network (bool, optional): If set, create network if it does not exists. Defaults to False.

        Raises:
            AttributeError: When network does not exist or can not be created.
        """
        try:
            networks: List[Network] = self._docker_client.networks.list(names=[network_name])  # type: ignore
        except Exception:
            networks = list()
        if networks:
            self.container_network = networks[0]
        elif not networks and auto_create_network:
            self.container_network = self._create_group_network(network_name)
        else:
            raise AttributeError

    @property
    def container_network_id(self) -> Optional[str]:
        """Container Short Id

        Returns:
            Optional[str]: container_id
        """
        return self.container_network.short_id

    def remove_network(self):
        """Cleanup created network"""
        self.container_network.remove()

    def _create_group_network(self, network_name: str, label: Dict[str, str] = dict()) -> Network:
        return self._docker_client.networks.create(  # type: ignore
            name=network_name,
            driver=NetworkConstants.DEFAULT_NETWORK_MODE,
            check_duplicate=True,
            internal=False,
            labels=label or None,
            enable_ipv6=False,
            attachable=True,
            scope=NetworkConstants.DEFAULT_NETWORK_SCOPE,
        )
