
from copy import copy
import time
from typing import Dict, List, Optional
from .configs.service_config import Config
from .generic_container.container import GenericContainer
from .models.config import RankedServices
from .models.running_container import RunningContainer
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)


class RunContainers:
    def __init__(self, services: RankedServices) -> None:
        self._ranked_container_services: RankedServices = services
        self.running_containers: RunningContainer = RunningContainer()
    
    def __enter__(self)-> RunningContainer:
        return self.run()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)

    def run(self):
        container_group_network: Optional[str] = None
        _running_containers: Dict[str, GenericContainer] = dict()
        try:
            ranks: List[int] = sorted(self._ranked_container_services.services)
            for rank in ranks:
                service = self._ranked_container_services.services[rank]
                container = GenericContainer(
                    image=service.image, 
                    command=service.command,
                    exposed_ports=service.exposed_ports,
                    environment_variables=service.environment,
                    volumes=service.volumes,
                    auto_remove=service.auto_remove,
                    remove_container=service.remove_container,
                )
                container.start()
                
                if service.log_wait_parameters:
                    if service.log_wait_parameters.log_line_regex:
                        container.wait_for_container_log(
                            log_line_regex=service.log_wait_parameters.log_line_regex,
                            wait_timeout=float(service.log_wait_parameters.wait_timeout or 60),
                            log_poll_interval=int(service.log_wait_parameters.poll_interval or 1)
                        )
                
                if service.http_wait_parameters:
                    container.with_waith_for_http(
                        exposed_port=service.http_wait_parameters.http_port,
                        status_code=service.http_wait_parameters.response_status_code
                    )
                
                container_id = container.get_wrapped_container().id
                if not container_group_network and container_id:
                    container_group_network = container.get_container_network(container_id=container_id)
                elif container_group_network and container_id:
                    _network_id = container.get_container_network(container_id=container_id)
                    if _network_id != container_group_network:
                        container.add_container_to_network(
                            container_id=container.get_wrapped_container().id, 
                            network_id=container_group_network
                        )
                
                _running_containers.update({service.name: container})
        except Exception as exc:
            self.stop_running_containers()
            logger.info("%s", exc)
            raise Exception
        logger.info("The following containers were started: %s", [x.name for x in self._ranked_container_services.services.values()])
        self.running_containers = RunningContainer(**_running_containers)
        return RunningContainer(**_running_containers)

    def stop_running_containers(self):
        _ranks: List[int] = sorted(self._ranked_container_services.services, reverse=True)
        for _rank in _ranks:
            container: GenericContainer = self.running_containers.containers[self._ranked_container_services.services[_rank].name]
            container.stop()
            logger.info("Successfully stopped container: %s: %s", self._ranked_container_services.services[_rank].name, container.get_wrapped_container().id)
            time.sleep(10)
        
        self.running_containers.containers.clear()