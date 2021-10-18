
from copy import deepcopy, copy
import time
from typing import Dict, List, Optional, Union
from .configs.service_config import Config
from .generic_container.container import GenericContainer
from .models.config import ItestConfigMapper
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)


class RunContainers:
    def __init__(self, services: Dict[int, ItestConfigMapper]) -> None:
        self._services: Dict[int, ItestConfigMapper] = services
        self.running_containers: Dict[str, ItestConfigMapper] = dict()
        self._spawned_container_ranks: Dict[str, int] = dict()
    
    def __enter__(self)-> Dict[str, ItestConfigMapper]:
        return self.run()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop_running_containers()
        if exc_tb and exc_type:
            logger.info("%s[%s]: %s", exc_type, exc_value, exc_tb)

    def run(self):
        container_group_network: str = None
        try:
            for rank, service in self._services.items():
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
                
                if not container_group_network:
                    container_group_network = container.get_container_network(container_id=container.get_wrapped_container().id)
                else:
                    _network_id = container.get_container_network(container_id=container.get_wrapped_container().id)
                    if _network_id != container_group_network:
                        container.add_container_to_network(
                            container_id=container.get_wrapped_container().id, 
                            network_id=container_group_network
                        )
                
                self.running_containers.update({service.name: container})
                self._spawned_container_ranks.update({rank: service.name})
        except Exception as exc:
            self.stop_running_containers()
            logger.info("%s", exc)
            raise Exception
        logger.info("The following containers were started: %s", [x.name for x in self._services.values()])
        _running_containers = copy(self.running_containers)
        return _running_containers

    def stop_running_containers(self):
        _ranks = list(self._spawned_container_ranks.keys())
        _ranks.sort(reverse=True)
        for _rank in _ranks:
            container = self.running_containers.get(self._spawned_container_ranks[_rank])
            container.stop()
            logger.info("Successfully stopped container: %s: %s", self._spawned_container_ranks[_rank], container.get_wrapped_container().id)
            time.sleep(10)
        
        self.running_containers.clear()
        self._spawned_container_ranks.clear()

if __name__ == "__main__":
    config = Config("docker-python/tests/config.yaml")
    config_content = config.get_config_services()
    # c = RunContainers(services=config_content)
    # c.run()
    # c.stop_running_containers()

    with RunContainers(services=config_content) as ch:
        print(ch)