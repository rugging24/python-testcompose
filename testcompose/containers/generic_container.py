import re
import socket
from docker.client import DockerClient
from typing import Any, ByteString, Dict, List, Optional, Tuple, Union
from docker.models.containers import Container
from docker.errors import APIError
from testcompose.containers.base_service_container import BaseServiceContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.models.container.running_container_attributes import RunningContainerAttributes
from testcompose.models.network.network import ContainerMappedPorts
from testcompose.waiters.endpoint_waiters import EndpointWaiters
from testcompose.waiters.log_waiters import LogWaiter
from testcompose.waiters.waiting_utils import WaitingUtils


class GenericContainer(BaseServiceContainer):
    """Generic container object to control the base properties of
    running containers. This class manipulates the base components
    of a container.

    Extra parameters can be provided as keyword arguments.

    Args:
        docker_client (DockerClient): docker client
    """

    def __init__(self, docker_client: DockerClient, **kwargs) -> None:
        super().__init__(docker_client)
        self._kwargs = kwargs

    @property
    def test_network(self) -> ContainerNetwork:
        return self._container_network

    @test_network.setter
    def test_network(self, network: ContainerNetwork) -> None:
        self._container_network = network

    @property
    def test_container(self) -> Container:
        return self._container

    @test_container.setter
    def test_container(self, container: Container) -> None:
        self._container = container

    @property
    def test_container_attr(self) -> RunningContainerAttributes:
        """Running container attributes

        Returns:
            RunningContainerAttributes: Container attribute object
        """
        return self._container_attr

    @test_container_attr.setter
    def test_container_attr(self, atrr: RunningContainerAttributes):
        """Running container attributes. Execute reload() to refresh this
        property.

        Args:
            atrr (RunningContainerAttributes): container attributes
        """
        self._container_attr = atrr

    def start(self) -> None:
        """Start a container"""
        if not self.docker_client.ping():
            raise RuntimeError("Docker Client not Running. Please check your docker settings and try again")
        try:
            self.test_container = self.docker_client.containers.run(
                image=self._image,
                command=self._command,
                detach=True,
                environment=self._environments,
                ports=self._ports,
                volumes=self._volumes,
                entrypoint=self._entry_point,
                auto_remove=True,
                remove=True,
                network=self._network,
                hostname=self._host_name,
                **self._kwargs,
            )
            WaitingUtils.container_status(self.test_container)
            self.reload()
            if self._http_waiter:
                mapped_http_port: Dict[str, str] = dict()
                mapped_http_port[str(self._http_waiter.http_port)] = self.get_exposed_port(
                    str(self._http_waiter.http_port)
                )
                EndpointWaiters.wait_for_http(self._http_waiter, mapped_http_port)
            LogWaiter.search_container_logs(self.test_container, self._log_waiter)
        except Exception as exc:
            print(exc)
            self.stop()

    def stop(self, force=True, delete_volume=True) -> None:
        """Stop a running container
        Args:
            force (bool, optional): [description]. Defaults to True.
            delete_volume (bool, optional): [description]. Defaults to True.
        """
        try:
            if self.test_container:
                self.test_container.remove(v=delete_volume, force=force)
        except APIError as exc:
            print(exc)

    def reload(self) -> None:
        """Reload the attributes of a running container"""
        self.test_container.reload()
        self.test_container_attr = RunningContainerAttributes(**self.test_container.attrs)
        if not WaitingUtils.container_status(self.test_container):
            raise RuntimeError("Container could not be started")

    def get_exposed_port(self, port: str) -> str:
        """Get host port bound to the container exposed port

        Args:
            port (str): container exposed port

        Returns:
            str: Host port bound to the container exposed port
        """
        if not port:
            return None  # type: ignore
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
        ports: Dict[str, Any] = self.test_container_attr.NetworkSettings.Ports
        #
        for port in ports:
            container_port = re.sub(f"[^0-9]", "", port)
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
        if self.test_container:
            return self.test_container.id
        return None

    def get_container_host_ip(self) -> str:
        """Container Host IP address

        Returns:
            str: container host IP Address
        """
        return socket.gethostbyname(socket.gethostname())

    def exe_command(self, command: Union[str, List[str]]) -> Tuple[int, ByteString]:
        """Execute a command inside a container once it started running.

        Args:
            command (Union[str, List[str]]): command to run in the container

        Raises:
            RuntimeError: when the container object is not set

        Returns:
            Tuple[int, ByteString]: A tuple of (exit_code, output)
        """
        if not self.test_container:
            raise RuntimeError("Container must already be running to exec a command")
        return self.test_container.exec_run(cmd=command)
