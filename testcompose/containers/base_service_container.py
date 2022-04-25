from abc import ABC, abstractmethod
from copy import deepcopy
import pathlib
import traceback
from typing import Any, Dict, List, Optional
from docker.client import DockerClient
from testcompose.containers.utils import ContainerUtils
from testcompose.models.client.registry_parameters import Login
from testcompose.models.config.config_services import Service
from testcompose.models.config.container_http_wait_parameter import HttpWaitParameter
from testcompose.models.config.container_log_wait_parameters import LogWaitParameter
from testcompose.models.config.volume import VolumeMapping
from docker.errors import ImageNotFound
from testcompose.models.config.volume import VolumeSourceTypes
from testcompose.models.container.running_container import RunningContainer


class BaseServiceContainer(ABC):
    """Container Builder"""

    def __init__(self, docker_client: DockerClient) -> None:
        self._image: str
        self._command: str
        self._entry_point: str
        self._host_name: str
        self._network: str
        self._http_waiter: HttpWaitParameter
        self._https_waiter: HttpWaitParameter
        self._log_waiter: LogWaitParameter
        self._registry = Login()
        self._environments: Dict[str, Any] = dict()
        self._ports: Dict[int, Any] = dict()
        self._volumes: Dict[str, Dict[str, str]] = dict()
        self._docker_host: Optional[str] = None
        self._image_pull_policy = 'ALWAYS_PULL'
        self.docker_client = docker_client

    @property
    def container_environment_variables(self) -> Dict[str, Any]:
        return self._container_environment_variables

    @container_environment_variables.setter
    def container_environment_variables(self, env: Dict[str, Any]) -> None:
        self._container_environment_variables = deepcopy(env)

    @property
    def docker_client(self) -> DockerClient:
        """Docker Client

        Returns:
            DockerClient: client object
        """
        return self._docker_client

    @docker_client.setter
    def docker_client(self, client: DockerClient):
        self._docker_client = client

    def with_service(
        self, service: Service, processed_containers_services: Dict[str, RunningContainer], network: str
    ) -> 'BaseServiceContainer':
        """
        The initialization method that converts a config
        service into a Generic Container. It leverages other
        internal _with methods to assign the complete container
        properties.

        Args:
            service (Service): a config service
            processed_containers_services (Dict[str, Any]): a dict of a service that
                had already been initiated and the container is running.
            network (str): the test network name, to attach all containers to.

        Returns:
            BaseServiceContainer
        """
        self._with_image(service.image)
        self._with_command(service.command)  # type: ignore
        (
            substituted_env_variables,
            modified_exposed_ports,
        ) = ContainerUtils.replace_container_config_placeholders(
            service_env_variables=service.environment,
            running_containers=processed_containers_services,
            service_name=service.name,
            exposed_ports=service.exposed_ports,
        )
        self._with_environment(substituted_env_variables)
        self._with_exposed_ports(list(set(modified_exposed_ports).union(set(service.exposed_ports))))
        self._with_wait_for_http(service.http_wait_parameters)  # type: ignore
        self._with_wait_for_https(service.https_wait_parameters)  # type: ignore
        self._with_volumes(service.volumes)
        self._with_entry_point(service.entrypoint)  # type: ignore
        self._with_log_waiter(service.log_wait_parameters)  # type: ignore
        self._with_host_name(service.name)
        self._with_network(network)
        return self

    def _with_network(self, network: str):
        self._network = network

    def _with_log_waiter(self, waiter: LogWaitParameter) -> None:
        self._log_waiter = waiter

    def _with_host_name(self, host: str) -> None:
        self._host_name = host

    def _with_exposed_ports(self, ports: Optional[List[str]]) -> None:
        """List of exposed port to be assigned random port
        numbers on the host. Random ports are exposed to the
        host. A fixed port can be assigned on the host by providing
        the port in the format **[host_port:container_port]**

        Args:
            ports (Optional[List[str]]): list of container exposed ports
        """
        if ports:
            for port in ports:
                _ports = str(port).split(":")
                if len(_ports) == 2:
                    self._ports[int(_ports[1])] = int(_ports[0])
                else:
                    self._ports[int(port)] = None

    def _with_wait_for_http(self, wait_parameter: HttpWaitParameter) -> None:
        self._http_waiter = wait_parameter

    def _with_wait_for_https(self, wait_parameter: HttpWaitParameter) -> None:
        self._https_waiter = wait_parameter

    def _with_volumes(self, volumes: Optional[List[VolumeMapping]]) -> None:
        """A list of volume mappings to be mounted in the container.

            VolumeMapping:
                host: host volume path or a docker volume name
                container: path to mount the host volume in the container
                mode: volume mode [ro|rw]
                source: source of the volume [filesystem|dockervolume]
                        filesystem: a file or directory to be mounted
                        dockervolume: a docker volume (existing or to be created)

        Args:
            volumes (Optional[List[VolumeMapping]]): Optional list of volumes to mount on the container
        """
        if volumes:
            for vol in volumes:
                host_bind: Optional[str] = None
                if vol.source == VolumeSourceTypes.DOCKER_VOLUME_SOURCE:
                    host_bind = vol.host
                elif vol.source == VolumeSourceTypes.FILESYSTEM_SOURCE:
                    host_bind = str(pathlib.Path(vol.host).absolute())
                if not host_bind:
                    raise ValueError("Volume source can only be one of local|docker")
                self._volumes[host_bind] = {"bind": vol.container, "mode": vol.mode}

    def _with_environment(self, env: Optional[Dict[str, Any]]) -> None:
        """Environment variables for running containers

        Args:
            env (Optional[Dict[str, Any]]): [description]
        """
        self.container_environment_variables = env or dict()
        if env:
            self._environments = deepcopy(env)

    def _with_image(self, image: str, image_pull_policy="ALWAYS_PULL") -> None:
        # TODO: Allow pull toggle
        self._image = image
        self._image_pull_policy = 'ALWAYS_PULL'

    def _with_command(self, command: str) -> None:
        self._command = command

    def with_registry(self, registry: Login) -> 'BaseServiceContainer':
        self._registry = registry
        return self

    def _with_entry_point(self, entry_point: str) -> None:
        self._entry_point = entry_point

    def build(self) -> 'BaseServiceContainer':
        """Construct a Generic container from a config service
        Args:
            docker_client (DockerClient): docker client
        """
        if self._registry:
            self.docker_client.login(**self._registry.dict())
        print(f"Pulling image {self._image}")
        if not self._image:
            raise ValueError("A valid Image entity must be provided")

        try:
            self.docker_client.images.get(name=self._image)
        except ImageNotFound:
            self.docker_client.images.pull(repository=self._image)
        except Exception:
            print(traceback.format_exc())
        return self

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self, force=True, delete_volume=True) -> None:
        raise NotImplementedError
