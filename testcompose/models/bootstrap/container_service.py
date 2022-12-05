from typing import Any, List, Optional, Dict
from pydantic import BaseModel, validator
from .container_log_wait_parameter import ContainerLogWaitParameter
from .container_volume import ContainerVolumeMap
from .container_http_wait_parameter import ContainerHttpWaitParameter


class ContainerService(BaseModel):
    name: str
    image: str
    exposed_ports: List[str]
    command: str = ''
    environment: Dict[str, Any] = dict()
    depends_on: List[str] = list()
    volumes: List[ContainerVolumeMap] = list()
    log_wait_parameters: Optional[ContainerLogWaitParameter] = None
    http_wait_parameters: Optional[ContainerHttpWaitParameter] = None
    https_wait_parameters: Optional[ContainerHttpWaitParameter] = None
    entrypoint: Optional[str] = None

    @validator('name')
    def validate_service_name(cls, v):
        if not v:
            raise AttributeError("Container Service name is required")
        return v

    @validator('image')
    def validate_image(cls, v):
        if not v:
            raise AttributeError("A valid image name is required")
        return v


class ContainerServices(BaseModel):
    """
    ConfigServices holds Dict of Service and their names
    Args:
        services: Dict[name, Service]
    """

    services: Dict[str, ContainerService]


class RankedContainerServices(BaseModel):
    """
    RankedConfigServices holds a dict of services ranked in the order they are to
    be started.
    Args:
        ranked_services: Dict[rank, name]
    """

    ranked_services: Dict[int, str] = dict()
