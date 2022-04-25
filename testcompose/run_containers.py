import time
from uuid import uuid4
from typing import Dict
from testcompose.client.base_docker_client import BaseDockerClient
from testcompose.containers.generic_container import GenericContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.log_setup import stream_logger
from testcompose.models.client.client_login import ClientFromEnv, ClientFromUrl
from testcompose.models.client.registry_parameters import Login
from testcompose.models.config.config_services import ConfigServices, RankedConfigServices, Service
from testcompose.models.container.running_container import RunningContainer, RunningContainers


logger = stream_logger(__name__)


class RunContainers(BaseDockerClient):
    """Run test containers

    Args:
        services (RankedServices): Ranked container services to be ran
        wait_time_between_container_start (float, optional): Default time to wait before spawning the next container.
                                                             This is aimed at preventing starting containers too earlier
                                                             before the container(s) they depend on has not fully started.
                                                             Especially when they do not have a log predicate to search for
                                                             or an http endpoint to check agains.
                                                             Defaults to 20.0.
        url_param (ClientFromUrl, optional): Url parameters for connecting to the docker daemon.
                                             Defaults to ClientFromUrl().
        env_param (ClientFromEnv, optional): Environment variables parameter required to connect to
                                             the docker daemon.
                                             Defaults to ClientFromEnv().
        registry_login_param ([type], optional): Parameter providing docker registry login details.
                                             Defaults to Login().
    """

    def __init__(
        self,
        config_services: ConfigServices,
        ranked_services: RankedConfigServices,
        wait_time_between_container_start: float = 20.0,
        registry_login_param=Login(),
        env_param: ClientFromEnv = ClientFromEnv(),
        url_param: ClientFromUrl = ClientFromUrl(),
    ) -> None:
        self._container_network: ContainerNetwork
        self._config_services: ConfigServices = config_services
        self._ranked_config_services: RankedConfigServices = ranked_services
        self.running_containers = RunningContainers()
        self._wait_time_between_container_start: float = wait_time_between_container_start
        self._registry_login_param: Login = registry_login_param
        self.initialise_docker_client(client_env_param=env_param, client_url_param=url_param)

    @property
    def running_containers(self) -> RunningContainers:
        """Running container objects

        Returns:
            RunningContainer: Running containers
        """
        return self._running_containers

    @running_containers.setter
    def running_containers(self, containers: RunningContainers):
        self._running_containers = containers

    @property
    def unique_container_label(self) -> str:
        """Unique test string label.

        Returns:
            str: unique label
        """
        return self._unique_container_label

    @unique_container_label.setter
    def unique_container_label(self, label: str):
        self._unique_container_label = label

    def __enter__(self) -> RunningContainers:
        return self.run()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)

    def run(self) -> RunningContainers:
        """Run all Generic Test Containers

        Raises:
            AttributeError: When current container being stated had a record it was already running.
            TimeoutError: When a predicate could not be found in the log over a specified period of time
            RuntimeError: When an http endpoint did not return the expected specified status code.
            Exception: When an Unknown error occured during the process of starting a container.

        Returns:
            RunningContainer: running containers
        """
        self.unique_container_label = uuid4().hex
        network_name = f"{self.unique_container_label}_network"
        self._container_network = ContainerNetwork(
            docker_client=self.docker_client, network_name=network_name
        )
        processed_containers_services: Dict[str, RunningContainer] = dict()
        try:
            for rank in sorted(self._ranked_config_services.ranked_services.keys()):
                service: Service = self._config_services.services[
                    self._ranked_config_services.ranked_services[rank]
                ]
                generic_container: GenericContainer = GenericContainer(docker_client=self.docker_client)
                generic_container.with_service(
                    service, processed_containers_services, self._container_network.network_name
                ).with_registry(self._registry_login_param).build()
                generic_container.test_network = self._container_network
                generic_container.start()
                running_container = RunningContainer(
                    service_name=service.name,
                    config_environment_variables=generic_container.container_environment_variables,
                    generic_container=generic_container,
                )
                processed_containers_services.update({service.name: running_container})
                time.sleep(self._wait_time_between_container_start)
        except Exception as exc:
            print(exc)
            self.stop_running_containers(RunningContainers(running_containers=processed_containers_services))
            logger.info("%s", exc)
            raise Exception
        logger.info("The following containers were started: %s", list(processed_containers_services.keys()))
        self.running_containers = RunningContainers(running_containers=processed_containers_services)
        return self.running_containers

    def stop_running_containers(self, running_containers: RunningContainers = RunningContainers()):
        """Stop all running containers"""
        try:
            _running_containers: RunningContainers = (
                running_containers if running_containers.running_containers else self.running_containers
            )
            for rank in sorted(self._ranked_config_services.ranked_services.keys(), reverse=True):
                service_name: str = self._ranked_config_services.ranked_services[rank]
                container: GenericContainer = _running_containers.running_containers[
                    service_name
                ].generic_container
                # [service_name].generic_container
                container.stop()
                if not self._container_network:
                    self._container_network = container.test_network
                logger.info(
                    "Successfully stopped container: %s(%s): %s",
                    service_name,
                    str(rank),
                    container.get_container_id(),
                )
                time.sleep(5)
        finally:
            if not self._container_network:
                raise AttributeError("Test network could not be removed. Still dangling ...")
            self._container_network.remove_network()
            logger.info("Run the ryuk container here!!!")
