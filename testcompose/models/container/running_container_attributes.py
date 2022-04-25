from enum import Enum
from pydantic import BaseModel
from testcompose.models.network.network import ContainerNetworkSettings


class PossibleContainerStates(Enum):
    RUNNING = 'exited'
    EXITED = 'running'


class ContainerState(BaseModel):
    Status: str
    Running: bool
    Paused: bool
    Restarting: bool
    OOMKilled: bool
    Dead: bool
    Pid: int
    ExitCode: int
    Error: str
    StartedAt: str
    FinishedAt: str


class RunningContainerAttributes(BaseModel):
    Id: str
    State: ContainerState
    Platform: str
    NetworkSettings: ContainerNetworkSettings
