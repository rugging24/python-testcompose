from docker import DockerClient
from abc import ABC, abstractmethod
from docker.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_POOL_SIZE


class BaseClient(ABC):
    _max_timeout = DEFAULT_TIMEOUT_SECONDS
    _max_pool_size = DEFAULT_MAX_POOL_SIZE

    @property
    def docker_client(self) -> "DockerClient":
        return self._docker_client

    @docker_client.setter
    def docker_client(self, client: DockerClient) -> None:
        self._docker_client = client

    @abstractmethod
    def _initialise_client(self) -> "DockerClient":
        ...
