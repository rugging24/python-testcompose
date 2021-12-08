from docker.client import DockerClient
from .base_client import BaseClient
from testcompose.models.client import ClientFromUrl


class UrlClient(BaseClient):
    def __init__(self, client_param: ClientFromUrl) -> None:
        """Client url parameters

        Args:
            client_param (ClientFromUrl): model class consisting of parameters for client connections with http url
        """
        super().__init__()
        self._docker_host = client_param.docker_host
        self._version = client_param.version
        self._timeout = client_param.timeout or BaseClient.max_timeout
        self._tls = client_param.tls
        self._user_agent = client_param.user_agent
        self._credstor_env = client_param.credstor_env
        self._use_ssh_client = client_param.use_ssh_client
        self._max_pool_size = client_param.max_pool_size or BaseClient.max_pool_size

        # self.docker_client = self.initialise_client()

    def initialise_client(self) -> None:
        """Init docker client

        Returns:
            DockerClient: docker client
        """
        self.docker_client = DockerClient(
            base_url=self._docker_host,
            version=self._version,
            timeout=self._timeout,
            tls=self._tls,
            user_agent=self._user_agent,
            credstor_env=self._credstor_env,
            use_ssh_client=self._use_ssh_client,
            max_pool_size=self._max_pool_size,
        )
