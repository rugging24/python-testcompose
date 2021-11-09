import time
from uuid import uuid4
from typing import Any, Dict, List, Tuple
from docker.client import DockerClient
from docker_python.containers.generic_container import GenericContainer
from docker_python.containers.container_network import ContainerNetwork
from .models.container import (
    RunningContainer,
    RunningContainerKeys, 
    RunningContainerEnvPrefixes
)
from .utils import Utils
from docker_python.models.config import (
    RankedServices, 
    ItestConfigMapper
)
from docker_python.models.client import (
    ClientFromEnv, ClientFromUrl, Login
)
from docker_python.client.client_from_env import EnvClient
from docker_python.client.client_from_url import UrlClient
from docker_python.models.container import ContainerParam
from testcontainers.core.utils import setup_logger


logger = setup_logger(__name__)


class RunContainers:
    def __init__(
        self, 
        services: RankedServices, 
        wait_time_between_container_start: float=20.0,
        url_param: ClientFromUrl=ClientFromUrl(), 
        env_param: ClientFromEnv=ClientFromEnv(),
        registry_login_param=Login()
    ) -> None:
        self._ranked_services: RankedServices = services
        self._running_containers: RunningContainer = RunningContainer()
        self._dependency_mapping: Dict[str, int]=dict()
        self._running_containers_extra_envs: Dict[str, Dict[str, Any]]=dict()
        self._wait_time_between_container_start: float = wait_time_between_container_start
        self._registry_login_param: Login = registry_login_param
        self.dclient = self.get_docker_client(env_param, url_param)

    def get_docker_client(self, env_param: ClientFromEnv, url_param: ClientFromUrl) -> DockerClient:
        try:
            client = EnvClient(env_param).docker_client if not url_param.docker_host \
                else UrlClient(url_param).docker_client
            assert client.ping()
            return client
        except Exception as exc:
            print(exc)
            raise Exception

    @property
    def dclient(self) -> DockerClient:
        return self._docker_client
    
    @dclient.setter
    def dclient(self, client: DockerClient) -> None:
        self._docker_client = client

    @property
    def running_containers(self) -> 'RunningContainer':
        return self._running_containers
    
    @running_containers.setter
    def running_containers(self, containers: RunningContainer):
        self._running_containers = containers
    
    def __enter__(self)-> RunningContainer:
        return self.run()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)
    
    def get_extra_dependency_envs(self, service: ItestConfigMapper, network_name: str=None) -> Dict[str, Dict[str, Any]]:
        _extra_env: Dict[str, Dict[str, Any]]=dict()
        _extra_env_dict_keys: Dict[str, Any] =dict()
        if service.name in self._dependency_mapping:
            raise AttributeError("A container can not have a cyclic dependency on itself")
            
        for depends in service.depends_on:
            if depends in self._dependency_mapping:
                _container: GenericContainer = self.running_containers.containers[depends]
                _extra_env_dict_keys.update({
                    f"{RunningContainerEnvPrefixes.INTERNAL_HOST}_{depends.upper()}": _container.get_container_ip(
                        network_mode=network_name
                    ),
                    f"{RunningContainerEnvPrefixes.EXTERNAL_HOST}_{depends.upper()}": _container.get_container_host_ip(),
                    f"{RunningContainerEnvPrefixes.MAPPED_PORTS}_{depends.upper()}":
                        _container.get_mapped_container_ports(
                            ports=self._ranked_services.services[(self._dependency_mapping[depends], depends)].exposed_ports
                        )
                })
        _extra_env_dict_keys.update({**service.environment})
        _extra_env.update({
            service.name: Utils.replace_pace_config_placeholders(
                env_config=_extra_env_dict_keys, 
                dependency_mapping=self._dependency_mapping,
                running_containers=self.running_containers
            )
        })
        logger.info("Found extra env variables: %s", _extra_env)
        return _extra_env

    def get_container_envs(self, container: GenericContainer, exposed_ports: List[str]) -> Dict[str, Any]:
        return {
            RunningContainerEnvPrefixes.EXTERNAL_HOST: container.get_container_host_ip(),
            RunningContainerEnvPrefixes.MAPPED_PORTS: container.get_mapped_container_ports(ports=exposed_ports)
        }

    def run(self):
        # _unique_label_prefix: str = uuid4().hex
        # network = ContainerNetwork(docker_client=self.dclient)
        # network.create_group_network(
        #     network_name=f"{_unique_label_prefix}_network",
        #     label={"name": f"{_unique_label_prefix}_network"}
        # )
        _running_containers: Dict[str, GenericContainer]=dict()
        try:
            ranks: List[Tuple[int, str]] = sorted(self._ranked_services.services)
            for rank, name in ranks:
                service = self._ranked_services.services[(rank, name)]
                _extra_envs: Dict[str, Dict[str, Any]] = self.get_extra_dependency_envs(
                    service #, str(network.container_network.name)
                )
                generic_container: GenericContainer = GenericContainer(
                    docker_client=self.dclient,
                    container_param=ContainerParam(
                        image=service.image,
                        exposed_ports=service.exposed_ports,
                        command=service.command,
                        entry_point=service.entrypoint,
                        environment_variables=_extra_envs.get(service.name),
                        volumes=service.volumes,
                        auto_remove=service.auto_remove,
                        remove_container=service.remove_container,
                        container_name=service.hostname,
                        registry_login_param=self._registry_login_param
                    )
                )
                generic_container.start()
                if (rank, service.name) in _running_containers:
                    logger.info("Duplicate name found in running containers : %s", service.name)
                    raise AttributeError

                if service.log_wait_parameters:
                    if service.log_wait_parameters.log_line_regex:
                        found: bool = generic_container.search_container_logs(
                            search_string=service.log_wait_parameters.log_line_regex,
                            timeout=float(service.log_wait_parameters.wait_timeout or 60),
                            interval=int(service.log_wait_parameters.poll_interval or 1)
                        )
                        if not found:
                            raise TimeoutError(
                                "container did not emit logs satisfying predicate in %.3f seconds" % 
                                float(service.log_wait_parameters.wait_timeout or 60)
                            )
                
                if service.http_wait_parameters:
                    if service.http_wait_parameters.http_port and \
                        service.http_wait_parameters.response_status_code:
                        response = generic_container.with_wait_for_http(
                            http_port=str(service.http_wait_parameters.http_port),
                            status_code=service.http_wait_parameters.response_status_code,
                            end_point=service.http_wait_parameters.end_point
                        )
                        if not response:
                            raise RuntimeError(f"Http check on port {service.http_wait_parameters.http_port} failed")

                _running_containers.update({name: generic_container})
                _con_extra_env: Dict[str, Any] = self.get_container_envs(generic_container, service.exposed_ports)
                generic_container.env = {**_con_extra_env, **_extra_envs.get(service.name, {})}
                self._dependency_mapping.update({name: rank})

                self._running_containers_extra_envs[service.name] = generic_container.env
                self.running_containers = RunningContainer(
                    **{
                        RunningContainerKeys.CONTAINERS: _running_containers,
                        RunningContainerKeys.EXTRA_ENVS: self._running_containers_extra_envs,
                        RunningContainerKeys.PRECEDENCE_MAP: self._dependency_mapping
                    }
                )
                time.sleep(self._wait_time_between_container_start)
                
        except Exception as exc:
            self.stop_running_containers()
            logger.info("%s", exc)
            raise Exception
        logger.info("The following containers were started: %s", [x.name for x in self._ranked_services.services.values()])
        return self.running_containers

    def stop_running_containers(self):
        _ranks: List[Tuple[int, str]] = sorted([(y, x) for x, y in self._dependency_mapping.items()], reverse=True)
        try:
            for _rank, _name in _ranks:
                container = self.running_containers.containers[_name]
                container.stop()
                logger.info(
                    "Successfully stopped container: %s(%s): %s", 
                    _name, str(_rank), container.get_container_id()
                )
                time.sleep(5)
        finally:
            print("Run the ryuk container here!!!")