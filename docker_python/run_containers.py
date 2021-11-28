import time
from uuid import uuid4
from typing import Any, Dict, List, Optional, Tuple
from docker.client import DockerClient
from docker_python.containers.generic_container import GenericContainer
from docker_python.containers.container_network import ContainerNetwork
from .models.container import RunningContainer, RunningContainerKeys, RunningContainerEnvPrefixes
from .containers.utils import ContainerUtils
from .models.config import RankedServices, ITestConfigServices
from .models.client import ClientFromEnv, ClientFromUrl, Login
from .models.container import ContainerParam
from .client.client_from_env import EnvClient
from .client.client_from_url import UrlClient
from .log_setup import stream_logger


logger = stream_logger(__name__)


class RunContainers:
    def __init__(
        self,
        services: RankedServices,
        wait_time_between_container_start: float = 20.0,
        url_param: ClientFromUrl = ClientFromUrl(),
        env_param: ClientFromEnv = ClientFromEnv(),
        registry_login_param=Login(),
    ) -> None:
        self._ranked_services: RankedServices = services
        self._running_containers: RunningContainer = RunningContainer()
        self._dependency_mapping: Dict[str, int] = dict()
        self._running_containers_extra_envs: Dict[str, Dict[str, Any]] = dict()
        self._wait_time_between_container_start: float = wait_time_between_container_start
        self._registry_login_param: Login = registry_login_param
        self.dclient = self.get_docker_client(env_param, url_param)
        self._container_network: Optional[ContainerNetwork] = None

    def get_docker_client(self, env_param: ClientFromEnv, url_param: ClientFromUrl) -> DockerClient:
        try:
            client = (
                EnvClient(env_param).docker_client
                if not url_param.docker_host
                else UrlClient(url_param).docker_client
            )
            assert client.ping()
            return client
        except Exception as exc:
            logger.error("%s", exc)
            raise Exception

    @property
    def dclient(self) -> DockerClient:
        return self._docker_client

    @dclient.setter
    def dclient(self, client: DockerClient) -> None:
        self._docker_client = client

    @property
    def running_containers(self) -> "RunningContainer":
        return self._running_containers

    @running_containers.setter
    def running_containers(self, containers: RunningContainer):
        self._running_containers = containers

    @property
    def unique_container_label(self) -> str:
        return self._unique_container_label

    @unique_container_label.setter
    def unique_container_label(self, label: str):
        self._unique_container_label = label

    def __enter__(self) -> RunningContainer:
        return self.run()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)

    def get_extra_dependency_envs(
        self, service: ITestConfigServices, network_name: Optional[str] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        extra_env: Dict[str, Dict[str, Any]] = dict()
        extra_env_dict_keys: Dict[str, Any] = dict()
        if service.name in self._dependency_mapping:
            raise AttributeError("A container can not have a cyclic dependency on itself")

        for depends in service.depends_on:
            if depends in self._dependency_mapping:
                container: GenericContainer = self.running_containers.containers[depends]
                extra_env_dict_keys.update(
                    {
                        f"{RunningContainerEnvPrefixes.INTERNAL_HOST}_{depends.upper()}": container.get_container_ip(
                            network_name=network_name
                        ),
                        f"{RunningContainerEnvPrefixes.EXTERNAL_HOST}_{depends.upper()}": container.get_container_host_ip(),
                        f"{RunningContainerEnvPrefixes.MAPPED_PORTS}_{depends.upper()}": container.get_mapped_container_ports(
                            ports=self._ranked_services.services[
                                (self._dependency_mapping[depends], depends)
                            ].exposed_ports
                        ),
                    }
                )
        extra_env_dict_keys.update({**service.environment})
        env_config, modified_exposed_ports = ContainerUtils.replace_container_config_placeholders(
            env_config=extra_env_dict_keys,
            dependency_mapping=self._dependency_mapping,
            running_containers=self.running_containers,
            unique_container_label=self.unique_container_label,
            service_name=service.name,
            exposed_ports=service.exposed_ports,
        )
        extra_env.update({service.name: env_config})
        logger.info("Found extra env variables: %s", extra_env)
        return extra_env, modified_exposed_ports

    def get_container_envs(self, container: GenericContainer, exposed_ports: List[str]) -> Dict[str, Any]:
        return {
            RunningContainerEnvPrefixes.EXTERNAL_HOST: container.get_container_host_ip(),
            RunningContainerEnvPrefixes.MAPPED_PORTS: container.get_mapped_container_ports(
                ports=exposed_ports
            ),
        }

    def run(self):
        self.unique_container_label = uuid4().hex
        auto_create_network = (
            self._ranked_services.network.auto_create
            if not self._ranked_services.network.use_random_network
            else self._ranked_services.network.use_random_network
        )
        network_name = (
            self._ranked_services.network.name
            if not self._ranked_services.network.use_random_network
            else f"{self.unique_container_label}_network"
        )
        self._container_network = ContainerNetwork(
            docker_client=self.dclient, network_name=network_name, auto_create_network=auto_create_network
        )
        running_containers: Dict[str, GenericContainer] = dict()
        try:
            ranks: List[Tuple[int, str]] = sorted(self._ranked_services.services)
            for rank, name in ranks:
                service = self._ranked_services.services[(rank, name)]
                extra_envs, _modified_container_exposed_ports = self.get_extra_dependency_envs(
                    service, self._container_network.network_name
                )
                generic_container: GenericContainer = GenericContainer(
                    docker_client=self.dclient,
                    container_param=ContainerParam(
                        image=service.image,
                        exposed_ports=_modified_container_exposed_ports,
                        command=service.command,
                        entry_point=service.entrypoint,
                        environment_variables=extra_envs.get(service.name),
                        volumes=service.volumes,
                        auto_remove=service.auto_remove,
                        remove_container=service.remove_container,
                        registry_login_param=self._registry_login_param,
                    ),
                    labels=[f"{self.unique_container_label}_{service.name}"],
                    hostname=f"{self.unique_container_label}_{service.name}",
                    network=self._container_network.network_name,
                )
                generic_container.start()
                running_containers.update({name: generic_container})
                con_extra_env: Dict[str, Any] = self.get_container_envs(
                    generic_container, service.exposed_ports
                )
                generic_container.env = {**con_extra_env, **extra_envs.get(service.name, {})}
                self._dependency_mapping.update({name: rank})

                self._running_containers_extra_envs[service.name] = generic_container.env
                self.running_containers = RunningContainer(
                    **{
                        RunningContainerKeys.CONTAINERS: running_containers,
                        RunningContainerKeys.EXTRA_ENVS: self._running_containers_extra_envs,
                        RunningContainerKeys.PRECEDENCE_MAP: self._dependency_mapping,
                    }
                )
                if (rank, service.name) in running_containers:
                    logger.info("Duplicate name found in running containers : %s", service.name)
                    raise AttributeError

                if service.log_wait_parameters:
                    if service.log_wait_parameters.log_line_regex:
                        found: bool = generic_container.search_container_logs(
                            search_string=service.log_wait_parameters.log_line_regex,
                            timeout=float(service.log_wait_parameters.wait_timeout or 60),
                            interval=int(service.log_wait_parameters.poll_interval or 1),
                        )
                        if not found:
                            raise TimeoutError(
                                "container %s did not emit logs satisfying predicate in %.3f seconds"
                                % (service.name, float(service.log_wait_parameters.wait_timeout or 60))
                            )

                if service.http_wait_parameters:
                    if (
                        service.http_wait_parameters.http_port
                        and service.http_wait_parameters.response_status_code
                    ):
                        response = generic_container.with_wait_for_http(
                            http_port=str(service.http_wait_parameters.http_port),
                            status_code=service.http_wait_parameters.response_status_code,
                            end_point=service.http_wait_parameters.end_point,
                        )
                        if not response:
                            raise RuntimeError(
                                f"Http check on port {service.http_wait_parameters.http_port} failed"
                            )

                time.sleep(self._wait_time_between_container_start)

        except Exception as exc:
            self.stop_running_containers()
            logger.info("%s", exc)
            raise Exception
        logger.info(
            "The following containers were started: %s",
            [x.name for x in self._ranked_services.services.values()],
        )
        return self.running_containers

    def stop_running_containers(self):
        _ranks: List[Tuple[int, str]] = sorted(
            [(y, x) for x, y in self._dependency_mapping.items()], reverse=True
        )
        try:
            for _rank, _name in _ranks:
                container: GenericContainer = self.running_containers.containers[_name]
                container.stop()
                logger.info(
                    "Successfully stopped container: %s(%s): %s",
                    _name,
                    str(_rank),
                    container.get_container_id(),
                )
                time.sleep(5)
        finally:
            if (
                any(
                    [
                        self._ranked_services.network.auto_create,
                        self._ranked_services.network.use_random_network,
                    ]
                )
                and self._container_network
            ):
                self._container_network.remove_network()
            logger.info("Run the ryuk container here!!!")
