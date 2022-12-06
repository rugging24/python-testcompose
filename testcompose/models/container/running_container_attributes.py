from pydantic import BaseModel
from testcompose.models.network.network import ContainerNetworkSettings
from dataclasses import dataclass


@dataclass(frozen=True)
class PossibleContainerStates:
    RUNNING: str = 'running'
    EXITED: str = 'exited'


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
