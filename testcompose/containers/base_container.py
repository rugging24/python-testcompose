from abc import abstractmethod
from copy import deepcopy
import pathlib
from typing import Any, Dict, List, Optional
from testcompose.containers.container_utils import ContainerUtils
from testcompose.models.bootstrap.container_service import ContainerService
from testcompose.models.bootstrap.container_http_wait_parameter import ContainerHttpWaitParameter
from testcompose.models.bootstrap.container_log_wait_parameter import ContainerLogWaitParameter
from testcompose.models.bootstrap.container_volume import ContainerVolumeMap
from testcompose.models.bootstrap.container_volume import VolumeSourceTypes
from testcompose.models.container.running_container import RunningContainer


class BaseContainer:
    def __init__(self) -> None:
        self._image_pull_policy: str = 'ALWAYS_PULL'

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, name: str) -> None:
        if not name:
            raise ValueError("A valid Image entity must be provided")
        self._image: str = name

    @property
    def command(self) -> str:
        return self._command

    @command.setter
    def command(self, command: str) -> None:
        self._command: str = command

    @property
    def entry_point(self) -> str:
        return self._entry_point

    @entry_point.setter
    def entry_point(self, entry_point: str) -> None:
        self._entry_point: str = entry_point

    @property
    def host_name(self) -> str:
        return self._host_name

    @host_name.setter
    def host_name(self, host_name: str) -> None:
        self._host_name: str = host_name

    @property
    def network(self) -> str:
        return self._network

    @network.setter
    def network(self, network: str) -> None:
        self._network: str = network

    @property
    def http_waiter(self) -> ContainerHttpWaitParameter:
        return self._http_waiter

    @http_waiter.setter
    def http_waiter(self, http_waiter: ContainerHttpWaitParameter) -> None:
        self._http_waiter: ContainerHttpWaitParameter = http_waiter

    @property
    def log_waiter(self) -> ContainerLogWaitParameter:
        return self._log_waiter

    @log_waiter.setter
    def log_waiter(self, log_waiter: ContainerLogWaitParameter) -> None:
        self._log_waiter: ContainerLogWaitParameter = log_waiter

    @property
    def ports(self) -> Dict[int, Any]:
        return self._ports

    @ports.setter
    def ports(self, ports: List[str]) -> None:
        self._ports: Dict[int, Any] = self._exposed_ports(ports)

    @property
    def container_environment_variables(self) -> Dict[str, Any]:
        return self._container_environment_variables

    @container_environment_variables.setter
    def container_environment_variables(self, env: Dict[str, Any]) -> None:
        self._container_environment_variables: Dict[str, Any] = deepcopy(env)

    @property
    def volumes(self) -> Dict[str, Dict[str, str]]:
        return self._volumes

    @volumes.setter
    def volumes(self, volumes: List[ContainerVolumeMap]) -> None:
        self._volumes: Dict[str, Dict[str, str]] = self._container_volumes(volumes)

    def with_service(
        self,
        service: ContainerService,
        processed_containers_services: Dict[str, RunningContainer],
        network: str,
    ) -> 'BaseContainer':
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
        self.image = service.image
        self.command = service.command
        (
            substituted_env_variables,
            modified_exposed_ports,
        ) = ContainerUtils.replace_container_config_placeholders(
            service_env_variables=service.environment,
            running_containers=processed_containers_services,
            service_name=service.name,
            exposed_ports=service.exposed_ports,
        )
        self.container_environment_variables = substituted_env_variables
        self.ports = modified_exposed_ports
        self.http_waiter = service.http_wait_parameters  # type: ignore
        self.volumes = service.volumes
        self.entry_point = service.entrypoint  # type: ignore
        self.log_waiter = service.log_wait_parameters  # type: ignore
        self.host_name = service.name
        self.network = network
        return self

    def _exposed_ports(self, ports: Optional[List[str]]) -> Dict[int, Any]:
        """List of exposed port to be assigned random port
        numbers on the host. Random ports are exposed to the
        host. A fixed port can be assigned on the host by providing
        the port in the format **[host_port:container_port]**

        Args:
            ports (Optional[List[str]]): list of container exposed ports
        """
        exposed_ports: Dict[int, Any] = dict()
        if ports:
            for port in ports:
                _ports: List[str] = str(port).split(":")
                if len(_ports) == 2:
                    exposed_ports[int(_ports[1])] = int(_ports[0])
                else:
                    exposed_ports[int(port)] = None
        return exposed_ports

    def _container_volumes(
        self, volumes: Optional[List[ContainerVolumeMap]] = None
    ) -> Dict[str, Dict[str, str]]:
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
        mapped_volumes: Dict[str, Dict[str, str]] = dict()
        if volumes:
            for vol in volumes:
                host_bind: Optional[str] = None
                if vol.source == VolumeSourceTypes.DOCKER_VOLUME_SOURCE:
                    host_bind = vol.host
                elif vol.source == VolumeSourceTypes.FILESYSTEM_SOURCE:
                    host_bind = str(pathlib.Path(vol.host).absolute())
                if not host_bind:
                    raise ValueError("Volume source can only be one of local|docker")
                mapped_volumes[host_bind] = {"bind": vol.container, "mode": vol.mode}
        return mapped_volumes

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self, force=True, delete_volume=True) -> None:
        raise NotImplementedError
