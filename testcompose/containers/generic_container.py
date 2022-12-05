from logging import Logger
import re
import socket
from docker.client import DockerClient
from typing import Any, ByteString, Dict, List, Optional, Tuple, Union
from docker.models.containers import Container
from docker.errors import APIError
from testcompose.containers.base_container import BaseContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.models.bootstrap.container_service import ContainerService
from testcompose.models.container.running_container import RunningContainer
from testcompose.models.container.running_container_attributes import RunningContainerAttributes
from testcompose.models.network.network import ContainerMappedPorts
from testcompose.waiters.endpoint_waiters import EndpointWaiters
from testcompose.waiters.log_waiters import LogWaiter
from testcompose.waiters.waiting_utils import WaitingUtils
from testcompose.log_setup import stream_logger


logger: Logger = stream_logger(__name__)


class GenericContainer(BaseContainer):
    def __init__(
        self,
        docker_client: DockerClient,
        network_name: str,
        service: ContainerService,
        processed_services: Dict[str, RunningContainer],
    ) -> None:
        super().__init__()
        self._docker_client: DockerClient = docker_client
        self.container_network = ContainerNetwork(docker_client, network_name)
        self.with_service(service, processed_services, self.container_network.name)  # type: ignore

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
        self._container_attr: RunningContainerAttributes = RunningContainerAttributes(**atrr)

    def start(self) -> None:
        """Start a container"""
        if not self._docker_client.ping():
            raise RuntimeError("Docker Client not Running. Please check your docker settings and try again")

        try:
            self.container = self._docker_client.containers.run(
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
            )  # type: ignore
            self.reload()
            LogWaiter.search_container_logs(self.container, self._log_waiter)  # type: ignore
            if self.http_waiter:
                mapped_http_port: Dict[str, str] = dict()
                mapped_http_port[str(self.http_waiter.http_port)] = self.get_exposed_port(  # type: ignore
                    str(self.http_waiter.http_port)
                )
                EndpointWaiters.wait_for_http(self._http_waiter, mapped_http_port)
        except Exception as exc:
            logger.error(exc)
            self.stop()

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

    def reload(self) -> None:
        """Reload the attributes of a running container"""
        self.container.reload()
        self.container_attr = self.container.attrs  # type: ignore
        if not WaitingUtils.container_status(self.container):
            raise RuntimeError("Container could not be started")

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
        #
        for port in ports:
            container_port = re.sub("[^0-9]", "", port)
            if container_port in exposed_ports and ports[port] and isinstance(ports[port], list):
                print(ports, ports[port])
                host_ports: ContainerMappedPorts = ContainerMappedPorts(**(ports[port][0]))
                print(host_ports)
                mapped_ports.update({container_port: host_ports.HostPort})
        return mapped_ports

    def get_container_id(self) -> Optional[str]:
        """Container id

        Returns:
            Optional[str]: Container Id
        """
        if self.container:
            return self.container.id
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
        return self.container.exec_run(cmd=command)
