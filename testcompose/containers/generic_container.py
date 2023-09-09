import re
import socket
from datetime import datetime
from logging import Logger
from time import sleep
from typing import Any, ByteString, Dict, List, Optional, Tuple, Union

from docker.client import DockerClient  # type: ignore
from docker.errors import APIError  # type: ignore
from docker.models.containers import Container  # type: ignore

from testcompose.containers.base_container import BaseContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.log_setup import stream_logger
from testcompose.models.container.running_container_attributes import (
    PossibleContainerStates,
    RunningContainerAttributes,
)
from testcompose.models.network.network import ContainerMappedPorts
from testcompose.waiters.endpoint_waiters import EndpointWaiters
from testcompose.waiters.log_waiters import LogWaiter
from testcompose.waiters.waiting_utils import is_container_still_running

logger: Logger = stream_logger(__name__)


class GenericContainer(BaseContainer):
    def __init__(self) -> None:
        super().__init__()

    @property
    def container_label(self) -> str:
        return self._container_label

    @container_label.setter
    def container_label(self, label: str) -> None:
        self._container_label = label

    @property
    def container_network(self) -> ContainerNetwork:
        return self._container_network

    @container_network.setter
    def container_network(self, network: ContainerNetwork) -> None:
        self._container_network: ContainerNetwork = network

    @property
    def container(self) -> Container:
        return self._container

    @container.setter
    def container(self, container: Container) -> None:
        self._container: Container = container

    @property
    def container_attr(self) -> RunningContainerAttributes:
        """Running container attributes

        Returns:
            RunningContainerAttributes: Container attribute object
        """
        return self._container_attr

    @container_attr.setter
    def container_attr(self, atrr: Dict[str, Any]) -> None:
        """Running container attributes. Execute reload() to refresh this
        property.

        Args:
            atrr (RunningContainerAttributes): container attributes
        """
        self._container_attr: RunningContainerAttributes = RunningContainerAttributes(**atrr)  # noqa: E501

    def start(self, docker_client: DockerClient) -> Container:  # type: ignore
        """Start a container"""
        if not docker_client.ping():
            raise RuntimeError(
                "Docker Client not Running. Please check your docker settings and try again"  # noqa: E501
            )  # noqa: E501

        return docker_client.containers.run(
            image=self.image,
            command=self.command,
            detach=True,
            environment=self.container_environment_variables,
            ports=self.ports,
            volumes=self.volumes,
            entrypoint=self.entry_point,
            auto_remove=True,
            remove=True,
            network=self.network,
            hostname=self.host_name,
            labels=[self.container_label],
        )  # type: ignore

    def check_container_health(self, docker_client: DockerClient, timeout: int = 120) -> None:  # noqa: E501
        start_time: datetime = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            logger.info(
                f"Waiting for containe:{self.container.name} status to \
                change from {self.container.status} to {PossibleContainerStates.RUNNING}"  # noqa: E501
            )
            self.container.reload()
            if self.container.status == PossibleContainerStates.RUNNING:
                logger.info(f"Container:{self.container.name} status changed to {self.container.status}")  # noqa: E501
                break
            sleep(2)

        self.reload(docker_client, self.get_container_id())
        if self.container.status != PossibleContainerStates.RUNNING:
            for line in self.container.logs(stream=True):
                logger.debug(line.decode())
            raise RuntimeError(f"Container is in an unwanted state {self.container.status}")  # noqa: E501

        self.reload(docker_client, self.get_container_id())

        LogWaiter.search_container_logs(docker_client, self.container, self.log_waiter)

        self.reload(docker_client, self.get_container_id())

        if self.http_waiter:
            mapped_http_port: Dict[str, str] = dict()
            mapped_http_port[str(self.http_waiter.http_port)] = self.get_exposed_port(  # type: ignore  # noqa: E501
                str(self.http_waiter.http_port)
            )
            EndpointWaiters.wait_for_http(
                docker_client,
                self.get_container_id(),  # type: ignore
                self.http_waiter,
                mapped_http_port,  # type: ignore
            )

    def stop(self, force=True, delete_volume=True) -> None:
        """Stop a running container
        Args:
            force (bool, optional): [description]. Defaults to True.
            delete_volume (bool, optional): [description]. Defaults to True.
        """
        try:
            if self.container:
                self.container.remove(v=delete_volume, force=force)
        except APIError as exc:
            logger.error(exc)

    def reload(self, docker_client, container_id) -> None:
        """Reload the attributes of a running container"""
        if is_container_still_running(docker_client, container_id):
            self.container.reload()
            self.container_attr = self.container.attrs  # type: ignore

    def get_exposed_port(self, port: str) -> Optional[str]:
        """Get host port bound to the container exposed port

        Args:
            port (str): container exposed port

        Returns:
            str: Host port bound to the container exposed port
        """
        if not port:
            return None
        return self._get_mapped_container_ports([port])[port]

    def _get_mapped_container_ports(self, exposed_ports: List[str]) -> Dict[str, str]:
        """Host port bound to the container returned as a k/v of the
        container exposed port as key and the host bound port as the value.

        Args:
            ports (List[str]): List of container exposed port to be mapped to host port

        Returns:
            Dict[str, str]: Mapped container-host ports.
        """
        mapped_ports: Dict[str, str] = dict()
        ports: Dict[str, Any] = self.container_attr.NetworkSettings.Ports
        for port in ports:
            container_port: str = re.sub("[^0-9]", "", port)
            if container_port in exposed_ports and ports[port] and isinstance(ports[port], list):  # noqa: E501
                host_ports: ContainerMappedPorts = ContainerMappedPorts(**(ports[port][0]))  # noqa: E501
                mapped_ports.update({container_port: host_ports.HostPort})
        return mapped_ports

    def get_container_id(self) -> Optional[str]:
        """Container id

        Returns:
            Optional[str]: Container Id
        """
        if self.container:
            return self.container.id  # type: ignore
        return None

    def get_container_host_ip(self) -> str:
        """Container Host IP address

        Returns:
            str: container host IP Address
        """
        return socket.gethostbyname(socket.gethostname())

    def exe_command(self, command: Union[str, List[str]]) -> Tuple[int, ByteString]:
        """Execute a command inside a container after it has started running.

        Args:
            command (Union[str, List[str]]): command to run in the container

        Raises:
            RuntimeError: when the container object is not set

        Returns:
            Tuple[int, ByteString]: A tuple of (exit_code, output)
        """
        if not self.container:
            raise RuntimeError("Container must already be running to exec a command")
        return self.container.exec_run(cmd=command)  # type: ignore
