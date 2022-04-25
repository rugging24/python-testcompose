from typing import Any, Dict
from pydantic import BaseModel


class RunningContainer(BaseModel):
    service_name: str
    config_environment_variables: Dict[str, Any]
    generic_container: Any  # this should be a GenericContainer type


class RunningContainers(BaseModel):
    running_containers: Dict[str, RunningContainer] = dict()
