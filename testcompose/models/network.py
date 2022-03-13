from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel


class HostPortMapping(BaseModel):
    HostIp: str
    HostPort: str


class ContainerNetworks(BaseModel):
    Aliases: Optional[List[str]] = None
    NetworkID: str
    EndpointID: str
    Gateway: str
    IPAddress: str


class ContainerNetworkSettings(BaseModel):
    Ports: Dict[str, Optional[List[HostPortMapping]]] = dict()
    Networks: Dict[str, ContainerNetworks]


@dataclass(frozen=True)
class NetworkConstants:
    DEFAULT_NETWORK_MODE: str = "bridge"
    DEFAULT_NETWORK_SCOPE: str = "local"
    DEFAULT_HOST_NETWORK: str = "host"
    DEFAULT_NONE_NETWORK: str = "none"
