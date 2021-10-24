from typing import Dict
from pydantic import BaseModel
from docker_python.generic_container.container import GenericContainer


class RunningContainer(BaseModel):
      containers: Dict[str, GenericContainer]= dict()