from pydantic import BaseModel
from dataclasses import dataclass


class VolumeMapping(BaseModel):
    host: str
    container: str
    mode: str
    source: str = "docker"


@dataclass(frozen=True)
class VolumeSourceTypes:
    LOCAL_SOURCE: str = "local"
    DOCKER_SOURCE: str = "docker"
