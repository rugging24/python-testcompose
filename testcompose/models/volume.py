from pydantic import BaseModel


class VolumeMapping(BaseModel):
    host: str
    container: str
    mode: str
