from logging import Logger
from uuid import uuid4
from typing import Dict, List

from testcompose.client.base_docker_client import BaseDockerClient
from testcompose.containers.generic_container import GenericContainer
from testcompose.containers.container_network import ContainerNetwork
from testcompose.housekeeping.clean_up_container import Housekeeping
from testcompose.log_setup import stream_logger
from testcompose.models.client.client_login import ClientFromEnv, ClientFromUrl
from testcompose.models.client.registry_parameters import Login
from testcompose.models.bootstrap.container_service import (
    ContainerServices,
    RankedContainerServices,
    ContainerService,
)
from testcompose.models.container.running_container import RunningContainer, RunningContainers
from docker.errors import APIError  # type: ignore


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
        registry_login_param=Login(),
        env_param: ClientFromEnv = ClientFromEnv(),
        url_param: ClientFromUrl = ClientFromUrl(),
    ) -> None:
        super(RunContainers, self).__init__(client_env_param=env_param, client_url_param=url_param)
        self._config_services: ContainerServices = config_services
        self._ranked_config_services: RankedContainerServices = ranked_services
        self.running_containers = RunningContainers()
        self.registry_login(login_credentials=registry_login_param)
        self._running_container_labels: List[str] = list()

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

    def __enter__(self) -> RunningContainers:
        try:
            return self.run_containers()
        except Exception:
            self.stop_running_containers()
            return RunningContainers()

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        try:
            self.stop_running_containers()
            if exc_tb and exc_type:
                logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)
        except Exception as exc:
            logger.info(exc.with_traceback(None))

    def run_containers(self) -> RunningContainers:
        self.unique_container_label = uuid4().hex
        network_name: str = f"{self.unique_container_label}_network"
        processed_containers_services: Dict[str, RunningContainer] = dict()
        self._running_container_labels.append(f"label={network_name}")

        for rank in sorted(self._ranked_config_services.ranked_services.keys()):
            service: ContainerService = self._config_services.services[
                self._ranked_config_services.ranked_services[rank]
            ]
            self.pull_docker_image(service.image)
            generic_container: GenericContainer = GenericContainer()
            generic_container.container_network = ContainerNetwork(
                self.docker_client, network_name, labels={"label": network_name}
            )
            generic_container.with_service(
                service,
                processed_containers_services,
                generic_container.container_network.name,  # type: ignore
            )
            generic_container.container_label = f"{self.unique_container_label}_{service.name}"
            self._running_container_labels.append(generic_container.container_label)
            try:
                log_wait_timeout = 120
                if service.log_wait_parameters:
                    log_wait_timeout = int((service.log_wait_parameters.wait_timeout_ms or 120000) / 1000)
                generic_container.container = generic_container.start(self.docker_client)
                generic_container.check_container_health(self.docker_client, timeout=log_wait_timeout)
                running_container: RunningContainer = RunningContainer(
                    service_name=service.name,
                    config_environment_variables=generic_container.container_environment_variables,
                    generic_container=generic_container,
                )
                processed_containers_services.update({service.name: running_container})
            except Exception as exc:
                logger.error(exc)
                self.stop_running_containers()
                raise APIError(exc)
        logger.info("The following containers were started: %s", list(processed_containers_services.keys()))
        self.running_containers = RunningContainers(running_containers=processed_containers_services)
        return self.running_containers

    def stop_running_containers(self) -> None:
        self._running_container_labels.sort(reverse=True)
        Housekeeping.perform_housekeeping(
            docker_client=self.docker_client, labels=self._running_container_labels
        )
