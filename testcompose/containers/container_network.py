from typing import Dict, List, Optional
from docker.models.networks import Network
from docker.client import DockerClient

from testcompose.models.network.network import DefaultNeworkDrivers


class ContainerNetwork:
    """Network management for running container.This class ensures
    all containers in the same test belong to the same network.
    Contians utility to create and cleanup network.

    Args:
        docker_client (DockerClient): Docker client
        network_name (str): Name of test network
    """

    def __init__(self, docker_client: DockerClient, network_name: str) -> None:
        self._docker_client = docker_client
        self._get_defined_network(network_name)

    @property
    def container_network(self) -> Network:
        """Network Object

        Returns:
            docker.models.networks.Network: container network object
        """
        return self._container_network

    @container_network.setter
    def container_network(self, network: Network) -> None:
        self._container_network = network

    @property
    def network_name(self) -> str:
        """Network Name

        Returns:
            str: Network Name
        """
        return self.container_network.name

    def _get_defined_network(self, network_name: str):
        """Identify or create container network
        Args:
            network_name (str): Network name

        Raises:
            AttributeError: When network does not exist or can not be created.
        """
        self.container_network = self._create_group_network(network_name)

    @property
    def container_network_id(self) -> Optional[str]:
        """Container Short Id

        Returns:
            Optional[str]: container_id
        """
        return self.container_network.short_id

    def remove_network(self):
        """Cleanup created network"""
        if self.container_network.name not in ['bridge', 'none', 'host']:
            self.container_network.remove()

    def _create_group_network(
        self,
        network_name: str,
        label: Dict[str, str] = dict(),
        driver: str = DefaultNeworkDrivers.DEFAULT_BRIDGE_NETWORK,
    ) -> Network:
        existing_networks: List[Network] = list()
        try:
            existing_networks = self._docker_client.networks.list(names=[network_name])
        except Exception:
            pass
        if not existing_networks:
            return self._docker_client.networks.create(
                name=network_name,
                driver=driver,
                check_duplicate=True,
                internal=False,
                labels=label or None,
                enable_ipv6=False,
                attachable=True,
                scope='local',
            )
        else:
            return existing_networks[0]
