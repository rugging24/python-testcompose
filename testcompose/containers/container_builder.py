from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from docker.client import DockerClient
from testcompose.models.container import ContainerParam
from testcompose.models.volume import VolumeMapping
from docker.errors import ImageNotFound


class ContainerBuilder(ABC):
    def __init__(self, container_param: ContainerParam) -> None:
        self._environments: Dict[str, Any] = dict()
        self._ports: Dict[int, Any] = dict()
        self._volumes: Dict[str, Dict[str, str]] = dict()
        self._docker_host: Optional[str] = None
        self.generic_container_param = container_param

    @property
    def generic_container_param(self) -> ContainerParam:
        return self._container_param

    @generic_container_param.setter
    def generic_container_param(self, param: ContainerParam) -> None:
        self._container_param = param

    @property
    def docker_client(self) -> DockerClient:
        return self._docker_client

    @docker_client.setter
    def docker_client(self, client: DockerClient):
        self._docker_client = client

    def with_exposed_ports(self, ports: Optional[List[str]]):
        if ports:
            for port in ports:
                _ports = str(port).split(":")
                if len(_ports) == 2:
                    self._ports[int(_ports[1])] = int(_ports[0])
                else:
                    self._ports[int(port)] = None

    def with_volumes(self, volumes: Optional[List[VolumeMapping]]):
        if volumes:
            for vol in volumes:
                self._volumes[vol.host] = {"bind": vol.container, "mode": vol.mode}

    def with_environment(self, env: Optional[Dict[str, Any]]):
        if env:
            for k, v in env.items():
                self._environments[k] = v

    def pull_image(self, image_pull_policy="Always_Pull"):
        # TODO: Allow pull toggle
        try:
            self.docker_client.images.get(name=self.generic_container_param.image)
        except ImageNotFound:
            self.docker_client.images.pull(repository=self.generic_container_param.image)

    def build(self, docker_client: DockerClient) -> None:
        self.docker_client = docker_client
        self.with_environment(self._container_param.environment_variables)
        self.with_volumes(self._container_param.volumes)
        self.with_exposed_ports(self._container_param.exposed_ports)
        if self.generic_container_param.registry_login_param.username:
            login = self.docker_client.login(**self.generic_container_param.registry_login_param.dict())
            print(login)
        print(f"Pulling image {self.generic_container_param.image}")
        self.pull_image()

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...
