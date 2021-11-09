# import re
# from datetime import datetime
# from time import sleep
# from typing import Any, Dict, List, Optional
# from requests import get
# from docker_python.models.volume import VolumeMapping
# from docker.api import APIClient
# from testcontainers.core.container import DockerContainer
# from testcontainers.core.waiting_utils import wait_container_is_ready
# from testcontainers.core.utils import setup_logger

# logger = setup_logger(__name__)

# class GenericContainer(DockerContainer):
#     def __init__(
#         self,
#         image: str,
#         exposed_ports: List[str],
#         command: Optional[str]=None,
#         entry_point: Optional[str]=None,
#         environment_variables: Optional[Dict[str, str]]= None,
#         volumes: Optional[List[VolumeMapping]]= None,
#         auto_remove: bool = True,
#         remove_container: bool = True,
#         container_name: Optional[str]=None,
#         **kwargs: Any
#     ) -> None:
#         super(GenericContainer, self).__init__(image)
#         if container_name:
#             self._name = container_name
#         if exposed_ports:
#             if not isinstance(exposed_ports, list):
#                 logger.info("Provided Values for exposed_ports must be of type List[int]")
#                 raise TypeError
#             self.with_exposed_ports(*exposed_ports)

#         if environment_variables:
#             self.with_ennvironments(environment_variables)
        
#         if command:
#             self.with_command(command)
        
#         if volumes:
#             if not isinstance(volumes, list):
#                 logger.info("Provided Values for volumes must be of type List[ItestConfigMapper]")
#                 raise TypeError

#             for volume in volumes:
#                 self.with_volume_mapping(
#                     host=volume.host, 
#                     container=volume.container,
#                     mode=volume.mode
#                 )
        
#         self.with_kwargs(
#             auto_remove=auto_remove, 
#             remove=remove_container,
#             entrypoint=entry_point,
#             **kwargs
#         )
    
#     def with_ennvironments(self, envs):
#         if not isinstance(envs, dict):
#             logger.info("Provided Values for environment_variables must be of type Dict[str, Any]")
#             raise TypeError
#         for k, v in envs.items():
#             self.with_env(key=k, value=v)

#     def __del__(self):
#         pass
    
#     def stop(self, force=True, delete_volume=True):
#         pass
#         # try:
#         #     super().stop(force=force, delete_volume=delete_volume)
#         # except:
#         #     super().__del__()
#         #     pass

#     def _container_info(self, container_id) -> Dict[str, Any]:
#         return APIClient().inspect_container(container=container_id)

#     # def get_container_network(self, container_id: str, network_driver:str ="bridge") -> Optional[str]:
#     #     container_info = self._container_info(container_id)
#     #     network_id = None
#     #     if container_info:
#     #         network_id = container_info.get('NetworkSettings', {}).get('Networks', {}).get(network_driver, {}).get('NetworkID')
#     #     return network_id

#     # def add_container_to_network(self, container_id, network_id: str) -> None:
#     #     APIClient().connect_container_to_network(
#     #         container_id, network_id
#     #     )
    
#     def get_container_external_ip(self) -> str:
#         return self.get_container_host_ip()
    
#     def get_mapped_container_ports(self, ports: List[str]) -> Dict[str, str]:
#         mapped_ports: Dict[str, str]=dict()
#         for port in ports:
#             mapped_ports.update({str(port): self.get_exposed_port(str(port))})
#         return mapped_ports
    
#     def get_container_internal_ip(self, network_driver="bridge") -> str:
#         container_info = self._container_info(container_id=self.get_wrapped_container().id)
#         if not container_info:
#             raise AttributeError(f"container {self.get_wrapped_container().id} info could not be obtained")
#         ip_address: str = container_info['NetworkSettings']['Networks'][network_driver]['IPAddress']
#         return ip_address
    
#     def get_container_status(self) -> str:
#         return self.get_wrapped_container().status
    
#     def get_container_id(self):
#         return self.get_wrapped_container().id
    
#     @wait_container_is_ready() # type: ignore
#     def wait_for_container_log(self, log_line_regex: str, wait_timeout: float=60.0, log_poll_interval: int=1) -> bool:
#         found = self.search_container_logs(
#             container=self,
#             search_string=log_line_regex, 
#             timeout=float(wait_timeout), 
#             interval=log_poll_interval
#         )
#         logger.info("%s", self.get_wrapped_container().logs().decode())
#         return found
    
#     @wait_container_is_ready() # type: ignore
#     def with_wait_for_http(self, exposed_port: int, status_code: int=200, end_point: str="/", server_startup_time: int=20) -> bool:
#         response_check: bool = True
#         for _ in range(0, 3):
#             sleep(server_startup_time)
#             try:
#                 mapped_port = self.get_exposed_port(port=exposed_port)
#                 host_ip = self.get_container_external_ip()
#                 site_url: str = f"http://{host_ip}:{mapped_port}/{end_point.lstrip('/')}"
#                 response = get(url=site_url.rstrip("/"))
#                 if response.status_code != status_code:
#                     logger.info("%s", self.get_wrapped_container().logs().decode())
#                     response_check = False
#                 break
#             except Exception as exc:
#                 response_check = False
#                 logger.error("HTTP_CHECK_ERROE: %s", exc)            
#         return response_check
    
#     def search_container_logs(self, container: DockerContainer, search_string: str, timeout: float=300.0, interval: int=1) -> bool:
#         if not isinstance(search_string, str):
#             raise ValueError

#         prog = re.compile(search_string, re.MULTILINE).search
#         start = datetime.now()
#         output: Optional[str] = None
#         while (datetime.now() - start).total_seconds() < timeout:
#             if self.get_container_status() == "exited":
#                 return False
#             output = prog(container._container.logs().decode()) # type: ignore
#             if output:
#                 return True
#             if (datetime.now() - start).total_seconds() > timeout:
#                 return False
#             sleep(interval)
#         return True if output else False