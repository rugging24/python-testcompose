from docker import DockerClient
from abc import ABC, abstractmethod
from docker.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_POOL_SIZE


class BaseClient(ABC):
    max_timeout = DEFAULT_TIMEOUT_SECONDS
    max_pool_size = DEFAULT_MAX_POOL_SIZE

    @property
    def docker_client(self) -> DockerClient:
        """Docker Client

        Returns:
            DockerClient: docker client object
        """
        return self._docker_client

    @docker_client.setter
    def docker_client(self, client: DockerClient) -> None:
        self._docker_client = client

    @abstractmethod
    def initialise_client(self) -> None:
        """This is the method that initializes the docker client and needs
        be implemented.
        """
        ...
