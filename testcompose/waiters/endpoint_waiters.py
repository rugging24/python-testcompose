import socket
from time import sleep
from typing import Dict
from requests import get
from testcompose.models.config.container_http_wait_parameter import HttpWaitParameter


class EndpointWaiters:
    @staticmethod
    def _get_container_host_ip() -> str:
        """The host IP where the container runs

        Returns:
            str: host IP
        """
        return socket.gethostbyname(socket.gethostname())

    @staticmethod
    def _check_endpoint(wait_parameter: HttpWaitParameter, exposed_ports: Dict[str, str]) -> None:
        """Endpoint health-check for a container. A running service
        with an exposed endpoint is queried and the response code is
        checked with the expected response code.

        Args:
            http_port (str): container service port
            status_code (int, optional): Defaults to 200.
            end_point (str, optional): Provided service endpoint. Defaults to "/".
            server_startup_time (int, optional): Expected wait time for the service to start. Defaults to 20.

        Returns:
            bool: Endpoint returned expected status code
        """
        response_check: bool = True
        site_url: str = "https://" if wait_parameter.use_https else "http://"
        for _ in range(0, 3):
            sleep(wait_parameter.startup_delay_time_ms / 1000)
            try:
                host = EndpointWaiters._get_container_host_ip()
                mapped_port = exposed_ports[str(wait_parameter.http_port)]
                site_url = site_url + f"{host}:{mapped_port}/{wait_parameter.end_point.lstrip('/')}"
                print(site_url)
                response = get(url=site_url.rstrip("/"))
                if response.status_code == wait_parameter.response_status_code:
                    break
            except Exception as exc:
                response_check = False
                print("HTTP_CHECK_ERROR: %s", exc)
        if not response_check:
            raise RuntimeError(f"Http check on port {wait_parameter.http_port} failed")
        return

    @staticmethod
    def wait_for_http(wait_parameter: HttpWaitParameter, exposed_ports: Dict[str, str]) -> None:
        if wait_parameter:
            EndpointWaiters._check_endpoint(wait_parameter, exposed_ports)
