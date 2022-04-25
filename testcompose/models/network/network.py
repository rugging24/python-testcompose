from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class NetworkComponents(BaseModel):
    Aliases: Optional[List[str]] = None
    NetworkID: str
    EndpointID: str
    Gateway: str
    IPAddress: str


class ContainerMappedPorts(BaseModel):
    HostIp: str
    HostPort: str


class ContainerNetworkSettings(BaseModel):
    Ports: Dict[str, Any] = dict()
    Networks: Dict[str, NetworkComponents]


@dataclass(frozen=True)
class DefaultNeworkDrivers:
    DEFAULT_BRIDGE_NETWORK = 'bridge'
    DEFAULT_HOST_NETWORK = 'host'
    DEFAULT_NULL_NETWORK = 'null'
