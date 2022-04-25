from dataclasses import dataclass
from pydantic import BaseModel, validator


@dataclass(frozen=True)
class VolumeSourceTypes:
    FILESYSTEM_SOURCE: str = "filesystem"
    DOCKER_VOLUME_SOURCE: str = "dockervolume"


class VolumeMapping(BaseModel):
    host: str
    container: str
    mode: str = 'ro'
    source: str = VolumeSourceTypes.DOCKER_VOLUME_SOURCE

    @validator('mode')
    def validate_mode(cls, v):
        assert str(v).lower() in ['ro', 'rw']
        return v

    @validator('source')
    def validate_source(cls, v):
        assert str(v).lower() in ['filesystem', 'dockervolume']
        return v

    @validator('host')
    def validate_host(cls, v):
        if not v:
            raise AttributeError("Volume Host option can not be empty or None")
        return v

    @validator('container')
    def validate_container(cls, v):
        if not v:
            raise AttributeError("Volume container option can not be empty or None")
        return v
