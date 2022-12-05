from logging import Logger
import time
from uuid import uuid4
from typing import Dict, Optional
from testcompose.client.base_docker_client import BaseDockerClient
from testcompose.containers.generic_container import GenericContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.log_setup import stream_logger
from testcompose.models.client.client_login import ClientFromEnv, ClientFromUrl
from testcompose.models.client.registry_parameters import Login
from testcompose.models.bootstrap.container_service import (
    ContainerServices,
    RankedContainerServices,
    ContainerService,
)
from testcompose.models.container.running_container import RunningContainer, RunningContainers


logger: Logger = stream_logger(__name__)


class RunContainers(BaseDockerClient):
    def __init_subclass__(cls, **kwargs) -> None:
        if cls is not RunContainers:
            raise TypeError("The class RunContainers can not be extended")
        return super().__init_subclass__()

    def __init__(
        self,
        config_services: ContainerServices,
        ranked_services: RankedContainerServices,
        wait_time_between_container_start: float = 20.0,
        registry_login_param=Login(),
        env_param: ClientFromEnv = ClientFromEnv(),
        url_param: ClientFromUrl = ClientFromUrl(),
    ) -> None:
        super(RunContainers, self).__init__(client_env_param=env_param, client_url_param=url_param)
        self._config_services: ContainerServices = config_services
        self._ranked_config_services: RankedContainerServices = ranked_services
        self.running_containers = RunningContainers()
        self._wait_time_between_container_start: float = wait_time_between_container_start
        self.registry_login(login_credentials=registry_login_param)

    @property
    def running_containers(self) -> RunningContainers:
        return self._running_containers

    @running_containers.setter
    def running_containers(self, containers: RunningContainers) -> None:
        self._running_containers: RunningContainers = containers

    @property
    def unique_container_label(self) -> str:
        return self._unique_container_label

    @unique_container_label.setter
    def unique_container_label(self, label: str) -> None:
        self._unique_container_label: str = label

    async def __aenter__(self) -> RunningContainers:
        return await self.run_containers()

    def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)

    async def run_containers(self) -> RunningContainers:
        self.unique_container_label = uuid4().hex
        network_name: str = f"{self.unique_container_label}_network"
        processed_containers_services: Dict[str, RunningContainer] = dict()

        try:
            for rank in sorted(self._ranked_config_services.ranked_services.keys()):
                service: ContainerService = self._config_services.services[
                    self._ranked_config_services.ranked_services[rank]
                ]
                self.pull_docker_image(service.image)
                generic_container: GenericContainer = GenericContainer(
                    docker_client=self.docker_client,
                    network_name=network_name,
                    service=service,
                    processed_services=processed_containers_services,
                )
                generic_container.start()
                running_container: RunningContainer = RunningContainer(
                    service_name=service.name,
                    config_environment_variables=generic_container.container_environment_variables,
                    generic_container=generic_container,
                )
                processed_containers_services.update({service.name: running_container})
                time.sleep(self._wait_time_between_container_start)
        except Exception as exc:
            self.stop_running_containers(RunningContainers(running_containers=processed_containers_services))
            logger.error("%s", exc)
            raise Exception
        logger.info("The following containers were started: %s", list(processed_containers_services.keys()))
        self.running_containers = RunningContainers(running_containers=processed_containers_services)
        return self.running_containers

    def stop_running_containers(self, running_containers: RunningContainers = RunningContainers()) -> None:
        container_network: Optional[ContainerNetwork] = None
        try:
            _running_containers: RunningContainers = (
                running_containers if running_containers.running_containers else self.running_containers
            )
            for rank in sorted(self._ranked_config_services.ranked_services.keys(), reverse=True):
                service_name: str = self._ranked_config_services.ranked_services[rank]
                if _running_containers.running_containers.get(service_name):
                    container: GenericContainer = _running_containers.running_containers[
                        service_name
                    ].generic_container
                    container.stop()
                    if not container_network:
                        container_network = container.container_network
                    logger.info(
                        "Successfully stopped container: %s(%s): %s",
                        service_name,
                        str(rank),
                        container.get_container_id(),
                    )
                    time.sleep(5)
        finally:
            if container_network:
                container_network.remove_network()
