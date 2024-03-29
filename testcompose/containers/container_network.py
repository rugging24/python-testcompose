from typing import Dict, Optional

from docker.client import DockerClient  # type: ignore
from docker.models.networks import Network  # type: ignore

from testcompose.models.network.network import DefaultNeworkDrivers


class ContainerNetwork:
    """Network management for running container.This class ensures
    all containers in the same test belong to the same network.
    Contians utility to create and cleanup network.

    Args:
        docker_client (DockerClient): Docker client
        network_name (str): Name of test network
    """

    def __init__(
        self, docker_client: DockerClient, network_name: str, labels: Dict[str, str] = dict()  # noqa: E501
    ) -> None:
        self._docker_client: DockerClient = docker_client
        self._assign_group_network(network_name, labels=labels)

    @property
    def network(self) -> Network:
        """Network Object

        Returns:
            docker.models.networks.Network: container network object
        """
        return self._container_network

    @network.setter
    def network(self, network: Network) -> None:
        self._container_network: Network = network

    @property
    def name(self) -> Optional[str]:
        return self.network.name  # type: ignore

    @property
    def network_id(self) -> Optional[str]:
        return self.network.short_id  # type: ignore

    def remove_network(self) -> None:
        try:
            if self.network.name not in ['bridge', 'none', 'host']:
                self.network.remove()
        except Exception as exc:
            print(f"Test network could not be removed. Still dangling ... {exc}")

    def _assign_group_network(
        self,
        network_name: str,
        labels: Dict[str, str] = dict(),
        driver: str = DefaultNeworkDrivers.DEFAULT_BRIDGE_NETWORK,
    ) -> None:
        try:
            self.network = (self._docker_client.networks.list(names=[network_name]))[0]  # type: ignore  # noqa: E501
        except Exception:
            self.network = self._docker_client.networks.create(
                name=network_name,
                driver=driver,
                check_duplicate=True,
                internal=False,
                labels=labels or None,
                enable_ipv6=False,
                attachable=True,
                scope='local',
            )  # type: ignore
