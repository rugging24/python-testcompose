from dataclasses import dataclass
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Tuple
from .volume import VolumeMapping
from .network import NetworkConstants


class LogWaitParameters(BaseModel):
    log_line_regex: str
    wait_timeout: str
    poll_interval: str


class HttpWaitParameters(BaseModel):
    http_port: int
    response_status_code: int
    startup_delay_time: int = 20
    end_point: str = "/"


class ITestConfigServices(BaseModel):
    name: str
    image: str
    exposed_ports: List[str]
    labels: List[str] = list()
    volumes: List[VolumeMapping] = list()
    depends_on: List[str] = list()
    environment: Dict[str, Any] = dict()
    auto_remove: bool = True
    remove_container: bool = True
    log_wait_parameters: Optional[LogWaitParameters] = None
    http_wait_parameters: Optional[HttpWaitParameters] = None
    command: Optional[str] = None
    entrypoint: Optional[str] = None


class ConfigCustomNetwork(BaseModel):
    name: str = NetworkConstants.DEFAULT_NETWORK_MODE
    auto_create: bool = False
    use_random_network: bool = False


class ITestConfig(BaseModel):
    services: List[ITestConfigServices]
    network: ConfigCustomNetwork = ConfigCustomNetwork()


class RankedServices(BaseModel):
    services: Dict[Tuple[int, str], ITestConfigServices]
    network: ConfigCustomNetwork


@dataclass(frozen=True)
class RankedServiceKey:
    SERVICES: str = "services"
    NETWORK: str = "network"
