from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass

from testcompose.models.client import Login
from testcompose.models.volume import VolumeMapping
from testcompose.models.network import ContainerNetworkSettings, NetworkConstants


class ContainerParam(BaseModel):
    image: str
    exposed_ports: List[str]
    command: Optional[str] = None
    entry_point: Optional[str] = None
    environment_variables: Optional[Dict[str, Any]] = None
    volumes: Optional[List[VolumeMapping]] = None
    auto_remove: bool = True
    remove_container: bool = True
    registry_login_param: Login = Login()


class RunningContainer(BaseModel):
    containers: Dict[str, Any] = dict()
    extra_envs: Dict[str, Dict[str, Any]] = dict()
    precedence_map: Dict[str, int] = dict()


class ContainerState(BaseModel):
    Status: str
    Running: bool
    Paused: bool
    Restarting: bool
    OOMKilled: bool
    Dead: bool
    ExitCode: int


class ContainerHostConfig(BaseModel):
    NetworkMode: str = NetworkConstants.DEFAULT_NETWORK_MODE


class RunningContainerAttributes(BaseModel):
    Id: str
    State: ContainerState
    Platform: str
    HostConfig: ContainerHostConfig
    NetworkSettings: ContainerNetworkSettings


@dataclass(frozen=True)
class RunningContainerKeys:
    CONTAINERS: str = "containers"
    EXTRA_ENVS: str = "extra_envs"
    PRECEDENCE_MAP: str = "precedence_map"


@dataclass(frozen=True)
class RunningContainerEnvPrefixes:
    INTERNAL_HOST: str = "DOCKER_PYTHON_INTERNAL_HOST"
    EXTERNAL_HOST: str = "DOCKER_PYTHON_EXTERNAL_HOST"
    MAPPED_PORTS: str = "DOCKER_PYTHON_MAPPED_PORTS"
