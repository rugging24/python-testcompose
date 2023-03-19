import docker  # type: ignore
from docker import DockerClient
from abc import ABC
from testcompose.models.client.client_login import ClientFromEnv, ClientFromUrl
from testcompose.models.client.registry_parameters import Login
from docker.errors import ImageNotFound  # type: ignore
import traceback
from testcompose.log_setup import stream_logger


logger = stream_logger(__name__)


class BaseDockerClient(ABC):
    def __init__(self, client_env_param: ClientFromEnv, client_url_param: ClientFromUrl) -> None:
        super(BaseDockerClient, self).__init__()
        _client_url_param: ClientFromUrl = ClientFromUrl()
        _client_env_param: ClientFromEnv = ClientFromEnv()

        if client_env_param:
            _client_env_param = client_env_param

        if client_url_param:
            _client_url_param = client_url_param

        self.docker_client = self._init_docker_client(
            client_url_param=_client_url_param, client_env_param=_client_env_param
        )

    @property
    def docker_client(self) -> DockerClient:
        return self._docker_client

    @docker_client.setter
    def docker_client(self, client: DockerClient) -> None:
        self._docker_client: DockerClient = client

    def _init_docker_client(
        self, *, client_url_param: ClientFromUrl, client_env_param: ClientFromEnv
    ) -> DockerClient:
        _docker_client: DockerClient = self._docker_client_from_env(client_env_param)
        if client_url_param.docker_host:
            _docker_client = self._docker_client_from_url(client_url_param)

        _docker_client.ping()
        return _docker_client

    def _docker_client_from_env(self, client_env_param: ClientFromEnv) -> DockerClient:
        return docker.from_env(
            version=client_env_param.version,
            timeout=client_env_param.timeout,
            max_pool_size=client_env_param.max_pool_size,
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

    def registry_login(self, login_credentials: Login) -> None:
        if login_credentials.registry:
            self.docker_client.login(**login_credentials.dict())

    def pull_docker_image(self, image_name: str) -> None:
        try:
            self.docker_client.images.get(name=image_name)
        except ImageNotFound:
            self.docker_client.images.pull(repository=image_name)
        except Exception:
            logger.error(traceback.format_exc())
