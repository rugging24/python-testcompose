from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from docker.client import DockerClient
from docker_python.models.client import Login
from docker_python.models.container import ContainerParam
from docker_python.models.volume import VolumeMapping
from docker.errors import ImageNotFound


class ContainerBuilder(ABC):
    def __init__(self, container_param: ContainerParam) -> None:
        self._environments: Dict[str, Any]= dict()
        self._ports: Dict[int, Any]= dict()
        self._volumes: Dict[str, Dict[str, str]]= dict()
        self._image: Optional[str]= None
        self._docker_host: Optional[str]= None
        self._command: Optional[str]= None
        self._name: Optional[str] = None
        self._login_param: Login= Login()
        self._host: Optional[str]= None
        self._container_param: ContainerParam = container_param
    
    @property
    def docker_client(self) -> DockerClient:
        return self._docker_client
    
    @docker_client.setter
    def docker_client(self, client: DockerClient):
        self._docker_client = client
    
    def with_registry_login(self, login: Login) -> 'ContainerBuilder':
        if login:
            self._login_param = login
        return self
    
    def with_exposed_ports(self, ports: Optional[List[str]]) -> 'ContainerBuilder':
        if ports:
            self._ports = {int(port): None for port in ports if port}
        return self
    
    def with_command(self, command: Optional[str]) -> 'ContainerBuilder':
        if command:
            self._command = command
        return self
    
    def with_volumes(self, volumes: Optional[List[VolumeMapping]]) -> 'ContainerBuilder':
        if volumes:
            for vol in volumes:
                self._volumes[vol.host] = {'bind': vol.container, 'mode': vol.mode}
        return self
    
    def with_environment(self, env: Optional[Dict[str, Any]]) -> 'ContainerBuilder':
        if env:
            for k, v in env.items():
                self._environments[k] = v
        return self
    
    def with_hostname(self, hostname: Optional[str]) -> 'ContainerBuilder':
        if hostname:
            self._host = hostname
        return self
    
    def with_container_name(self, name: Optional[str]) -> 'ContainerBuilder':
        if name:
            self._name = name
        return self
    
    def with_image(self, image: str):
        if image:
            self._image = image
    
    def pull_image(self, always_pull=False):
        # ToDo allow pull toggle
        try:
            self.docker_client.images.get(name=self._image)
        except ImageNotFound:
            self.docker_client.images.pull(repository=self._image)
    
    def build(self, docker_client: DockerClient) -> None:
        # print("----------------------------")
        # print(self._container_param)
        # print("----------------------------")
        self.docker_client = docker_client
        self.with_container_name(self._container_param.container_name)
        self.with_environment(self._container_param.environment_variables)     
        self.with_volumes(self._container_param.volumes)
        self.with_command(self._container_param.command)
        self.with_exposed_ports(self._container_param.exposed_ports)
        self.with_registry_login(self._container_param.registry_login_param)
        self.with_image(self._container_param.image)
        if self._login_param.username:
            login = self.docker_client.login(**self._login_param.dict())
            print(login)
        print(f"Pulling image {self._image}")
        self.pull_image()
    
    @abstractmethod
    def start(self):
        ...
    
    @abstractmethod
    def stop(self):
        ...