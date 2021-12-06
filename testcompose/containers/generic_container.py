import re
import socket
from docker.client import DockerClient
from requests import get
from datetime import datetime
from time import sleep
from typing import Any, ByteString, Dict, List, Match, Optional, Tuple, Union
from docker.models.containers import Container
from docker.errors import APIError
from testcompose.models.network import HostPortMapping, NetworkConstants
from testcompose.containers.container_builder import ContainerBuilder
from testcompose.models.container import ContainerParam, RunningContainerAttributes


class GenericContainer(ContainerBuilder):
    """Generic container object to control the base properties of
    running containers. This class manipulates the base components
    of a container.

    Parameters not part of the **ContainerParam** object can be provided as
    keyword arguments.


    Args:
        docker_client (DockerClient): docker client
        container_param (ContainerParam): container parameter for a given service
    """

    def __init__(self, docker_client: DockerClient, container_param: ContainerParam, **kwargs) -> None:
        super().__init__(container_param)
        self._kwargs = kwargs
        self.env = container_param.environment_variables or dict()
        self.build(docker_client=docker_client)

    @property
    def env(self) -> Dict[str, Any]:
        """Container environment variables

        Returns:
            Dict[str, Any]: environment variables
        """
        return self._env

    @env.setter
    def env(self, env_variable: Dict[str, Any]):
        self._env = env_variable

    @property
    def container(self) -> Container:
        return self._container

    @container.setter
    def container(self, _container) -> None:
        self._container = _container

    @property
    def get_container_attr(self) -> RunningContainerAttributes:
        """Running container attributes

        Returns:
            RunningContainerAttributes: Container attribute object
        """
        return self._container_attr

    @get_container_attr.setter
    def get_container_attr(self, atrr: RunningContainerAttributes):
        self._container_attr = atrr

    def start(self) -> None:
        """Start a container"""
        try:
            if self.docker_client:
                self.container = self.docker_client.containers.run(
                    image=self.generic_container_param.image,
                    command=self.generic_container_param.command,
                    detach=True,
                    environment=self._environments,
                    ports=self._ports,
                    volumes=self._volumes,
                    entrypoint=self.generic_container_param.entry_point,
                    auto_remove=self.generic_container_param.auto_remove,
                    remove=self.generic_container_param.remove_container,
                    **self._kwargs,
                )
                self.reload()
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
            if self.container:
                self.container.remove(v=delete_volume, force=force)
        except APIError as exc:
            print(exc)

    def reload(self) -> None:
        """Reload the attributes of a running container"""
        self.container.reload()
        self.get_container_attr = RunningContainerAttributes(**self.container.attrs)
        self.wait_on_condition()

    def get_exposed_port(self, port: str) -> str:
        """Get host port bound to the container exposed port

        Args:
            port (str): container exposed port

        Returns:
            str: Host port bound to the container exposed port
        """
        return self.get_mapped_container_ports([port])[port]

    def get_mapped_container_ports(self, ports: List[str]) -> Dict[str, str]:
        """Host port bound to the container returns as a k/v of the
        container exposed port as key and the host bound port as the value.

        Args:
            ports (List[str]): List of container exposed port to be mapped to host port

        Returns:
            Dict[str, str]: Mapped container-host ports.
        """
        mapped_ports: Dict[str, str] = dict()
        _ports: Dict[str, Optional[List[HostPortMapping]]] = self.get_container_attr.NetworkSettings.Ports
        for cport, hport in _ports.items():
            host_port = re.sub(f"[^0-9]", "", cport)
            if host_port in ports and hport:
                mapped_ports.update({host_port: str(hport[0].HostPort)})
        return mapped_ports

    def get_container_id(self) -> Optional[str]:
        """Container id

        Returns:
            Optional[str]: Container Id
        """
        if self.container:
            return self.container.id
        return None

    def get_container_ip(self, network_name=NetworkConstants.DEFAULT_NETWORK_MODE) -> str:
        """Running container IP address

        Args:
            network_name ([type], optional): [description]. Defaults to NetworkConstants.DEFAULT_NETWORK_MODE.

        Raises:
            ValueError: when network_name is not provided

        Returns:
            str: container IP Address
        """
        if not network_name:
            raise ValueError("Docker network name must be provided!!")
        _networks = self.get_container_attr.NetworkSettings.Networks[network_name]

        return _networks.IPAddress

    def exe_command(self, command: Union[str, List[str]]) -> Tuple[int, ByteString]:
        """Execute a command inside a container once it started running.

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

    def search_container_logs(self, search_string: str, timeout: float = 300.0, interval: int = 1) -> bool:
        """Search for a given predicate in the container log. Useful to check if a
        container is running and healthy

        Args:
            search_string (str): predicate to search in the log
            timeout (float, optional): Defaults to 300.0.
            interval (int, optional): Defaults to 1.

        Raises:
            ValueError: if a non string predicate is passed

        Returns:
            bool: True if the log contains the provided predicate
        """
        if not isinstance(search_string, str):
            raise ValueError

        prog = re.compile(search_string, re.MULTILINE).search
        start = datetime.now()
        output: Optional[Match[str]] = None
        while (datetime.now() - start).total_seconds() < timeout:
            output = prog(self.container.logs().decode())
            if output:
                return True
            if (datetime.now() - start).total_seconds() > timeout:
                return False
            sleep(interval)
        print("%s", self.container.logs().decode())
        return True if output else False

    @staticmethod
    def get_container_host_ip() -> str:
        """The host IP where the container runs

        Returns:
            str: host IP
        """
        return socket.gethostbyname(socket.gethostname())

    def with_wait_for_http(
        self, http_port: str, status_code: int = 200, end_point: str = "/", server_startup_time: int = 20
    ) -> bool:
        """Endpoint health-check for a container. A running service
        with an exposed endpoint is queried and the response code is
        checked with the expected response code.

        Args:
            http_port (str): container service port
            status_code (int, optional): Defaults to 200.
            end_point (str, optional): Provided service endpoint. Defaults to "/".
            server_startup_time (int, optional): Expected wait time for the service to start. Defaults to 20.

        Returns:
            bool: Endpoint returned expected status code
        """
        response_check: bool = True
        for _ in range(0, 3):
            sleep(server_startup_time)
            try:
                site_url = f"http://{self.get_container_host_ip()}:{self.get_exposed_port(port=http_port)}/{end_point.lstrip('/')}"
                response = get(url=site_url.rstrip("/"))
                if response.status_code != status_code:
                    print("%s", self.container.logs().decode())
                    response_check = False
                break
            except Exception as exc:
                response_check = False
                print("HTTP_CHECK_ERROE: %s", exc)
        return response_check

    def wait_on_condition(self, status="running", delay=0.1, timeout=40):
        """Method useful for checking a running container status to
        allow for fetching the latest attribute from the container

        Args:
            status (str, optional): Status to check for. Defaults to "running".
            delay (float, optional): Delay time before the next check. Defaults to 0.1.
            timeout (int, optional): Defaults to 40.
        """

        def condition() -> bool:
            """Container emits expected status

            Returns:
                bool: container matches expected status
            """
            return status == self.get_container_attr.State.Status

        start = datetime.now()
        while not condition():
            if (datetime.now() - start).total_seconds() > timeout:
                raise AssertionError("Container status %s not obtained after 40secx" % status)
            sleep(delay)
        print(f"Found Status {self.get_container_attr.State.Status}")
        return
