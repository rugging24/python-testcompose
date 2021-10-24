from dataclasses import dataclass
from pydantic import BaseModel
from typing import Dict, List, Optional
from .volume import VolumeMapping


class LogWaitParameters(BaseModel):
    log_line_regex: str
    wait_timeout: str
    poll_interval: str


class HttpWaitParameters(BaseModel):
    http_port: int
    response_status_code: int


class ItestConfigMapper(BaseModel):
    name: str
    image: str
    spawn_rank: int
    exposed_ports: List[int]=list()
    volumes: List[VolumeMapping]=list()
    depends_on: List[str]=list()
    environment: Dict[str, str]=dict()
    auto_remove: bool=True
    remove_container: bool=True
    log_wait_parameters: Optional[LogWaitParameters]=None
    http_wait_parameters: Optional[HttpWaitParameters]=None
    command: Optional[str]=None


class Services(BaseModel):
    services: List[ItestConfigMapper]

class RankedServices(BaseModel):
    services: Dict[int, ItestConfigMapper]

@dataclass(frozen=True)
class RankedServiceKey:
    SERVICES: str='services'