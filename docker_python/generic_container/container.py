
from typing import Any, Dict, List, Optional, Union
from requests import get
from docker.api import APIClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs, wait_container_is_ready
from docker_python.models.volume import VolumeMapping
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)

class GenericContainer(DockerContainer):
    def __init__(
        self,
        image: str,
        exposed_ports: List[int],
        command: Optional[str]=None,
        environment_variables: Optional[Dict[str, str]]= None,
        volumes: Optional[List[VolumeMapping]]= None,
        auto_remove: bool = True,
        remove_container: bool = True,
        **kwargs: Any
    ) -> None:
        super(GenericContainer, self).__init__(image)
        if exposed_ports:
            if not isinstance(exposed_ports, list):
                logger.info("Provided Values for exposed_ports must be of type List[int]")
                raise TypeError
            self.with_exposed_ports(*exposed_ports)

        if environment_variables:
            if not isinstance(environment_variables, dict):
                logger.info("Provided Values for environment_variables must be of type Dict[str, Any]")
                raise TypeError
            for k, v in environment_variables.items():
                self.with_env(key=k, value=v)
        
        if command:
            self.with_command(command)
        
        if volumes:
            if not isinstance(volumes, list):
                logger.info("Provided Values for volumes must be of type List[str]")
                raise TypeError
            # mapped: List[VolumeMapping] = [
            #     VolumeMapping(k) 
            #     for k in volumes
            # ]
            for volume in volumes:
                self.with_volume_mapping(
                    host=volume.host, 
                    container=volume.container,
                    mode=volume.mode
                )
        
        self.with_kwargs(
            auto_remove=auto_remove, 
            remove=remove_container,
            **kwargs
        )

    def __del__(self):
        pass
    
    def stop(self, force=True, delete_volume=True):
        try:
            super().stop(force=force, delete_volume=delete_volume)
        except:
            super().__del__()
            pass

    def get_container_network(self, container_id: str) -> Any:
        container_info = APIClient().inspect_container(container=container_id)
        network_id = None
        if container_info:
            network_id = container_info.get('NetworkSettings', {}).get('Networks', {}).get('bridge', {}).get('NetworkID')
        return network_id

    def add_container_to_network(self, container_id, network_id: str) -> None:
        APIClient().connect_container_to_network(
            container_id, network_id
        )
    
    def get_container_external_ip(self) -> str:
        return self.get_container_host_ip()
    
    @wait_container_is_ready() # type: ignore
    def wait_for_container_log(self, log_line_regex: str, wait_timeout: float=60.0, log_poll_interval: int=1) -> None:
        wait_for_logs(
            container=self,
            predicate=log_line_regex, 
            timeout=wait_timeout, 
            interval=log_poll_interval
        )
        logger.info("%s", self.get_wrapped_container().logs().decode())
    
    @wait_container_is_ready() # type: ignore
    def with_waith_for_http(self, exposed_port: int, status_code: int=200) -> bool:
        mapped_port = self.get_exposed_port(port=exposed_port)
        host_ip = self.get_container_host_ip()
        response = get(url=f'{host_ip}:{mapped_port}')
        if response.status_code != status_code:
            raise RuntimeError
        return True