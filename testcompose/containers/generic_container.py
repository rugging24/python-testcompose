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
    def __init__(self, docker_client: DockerClient, container_param: ContainerParam, **kwargs) -> None:
        super().__init__(container_param)
        self._kwargs = kwargs
        self.env = container_param.environment_variables or dict()
        self.build(docker_client=docker_client)

    @property
    def env(self) -> Dict[str, Any]:
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
        return self._container_attr

    @get_container_attr.setter
    def get_container_attr(self, atrr: RunningContainerAttributes):
        self._container_attr = atrr

    def start(self) -> None:
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
        try:
            if self.container:
                self.container.remove(v=delete_volume, force=force)
        except APIError as exc:
            print(exc)

    def reload(self) -> None:
        self.container.reload()
        self.get_container_attr = RunningContainerAttributes(**self.container.attrs)
        self.wait_on_condition()

    def get_exposed_port(self, port: str) -> str:
        return self.get_mapped_container_ports([port])[port]

    def get_mapped_container_ports(self, ports: List[str]) -> Dict[str, str]:
        mapped_ports: Dict[str, str] = dict()
        _ports: Dict[str, Optional[List[HostPortMapping]]] = self.get_container_attr.NetworkSettings.Ports
        for cport, hport in _ports.items():
            host_port = re.sub(f"[^0-9]", "", cport)
            if host_port in ports and hport:
                mapped_ports.update({host_port: str(hport[0].HostPort)})
        return mapped_ports

    def get_container_id(self) -> Optional[str]:
        if self.container:
            return self.container.id
        return None

    def get_container_ip(self, network_name=NetworkConstants.DEFAULT_NETWORK_MODE) -> str:
        if not network_name:
            raise ValueError("Docker network name must be provided!!")
        _networks = self.get_container_attr.NetworkSettings.Networks[network_name]

        return _networks.IPAddress

    def exe_command(self, command: Union[str, List[str]]) -> Tuple[int, ByteString]:
        if not self.container:
            raise RuntimeError("Container must already be running to exec a command")
        return self.container.exec_run(cmd=command)

    def search_container_logs(self, search_string: str, timeout: float = 300.0, interval: int = 1) -> bool:
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
        return socket.gethostbyname(socket.gethostname())

    def with_wait_for_http(
        self, http_port: str, status_code: int = 200, end_point: str = "/", server_startup_time: int = 20
    ) -> bool:
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
        def condition():
            return status == self.get_container_attr.State.Status

        start = datetime.now()
        while not condition():
            if (datetime.now() - start).total_seconds() > timeout:
                raise AssertionError("Container status %s not obtained after 40secx" % status)
            sleep(delay)
        print(f"Found Status {self.get_container_attr.State.Status}")
        return
