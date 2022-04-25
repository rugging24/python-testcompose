import docker
from docker import DockerClient
from abc import ABC
from docker.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_POOL_SIZE


from testcompose.models.client.client_login import ClientFromEnv, ClientFromUrl


class BaseDockerClient(ABC):
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

    def initialise_docker_client(
        self,
        client_env_param: ClientFromEnv = ClientFromEnv(),
        client_url_param: ClientFromUrl = ClientFromUrl(),
    ) -> None:
        if client_url_param.docker_host:
            self.docker_client = self._docker_client_from_url(client_url_param)
        else:
            self.docker_client = self._docker_client_from_env(client_env_param)

        self.docker_client.ping()

    def _docker_client_from_env(self, client_env_param: ClientFromEnv) -> DockerClient:
        return docker.from_env(
            version=client_env_param.version,
            timeout=client_env_param.timeout or BaseDockerClient.max_timeout,
            max_pool_size=client_env_param.max_pool_size or BaseDockerClient.max_pool_size,
            use_ssh_client=client_env_param.use_ssh_client,
            ssl_version=client_env_param.ssl_version,
            assert_hostname=client_env_param.assert_hostname,
            environment=client_env_param.environment,
        )

    def _docker_client_from_url(self, client_url_param: ClientFromUrl) -> DockerClient:
        return DockerClient(
            base_url=client_url_param.docker_host,
            version=client_url_param.version,
            timeout=client_url_param.timeout,
            tls=client_url_param.tls,
            user_agent=client_url_param.user_agent,
            credstor_env=client_url_param.credstor_env,
            use_ssh_client=client_url_param.use_ssh_client,
            max_pool_size=client_url_param.max_pool_size,
        )
