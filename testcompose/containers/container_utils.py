import re
import socket
from copy import copy, deepcopy
from typing import Any, Dict, List, Optional, Tuple
from testcompose.models.container.supported_placeholders import SupportedPlaceholders
from testcompose.models.container.running_container import RunningContainer


class ContainerUtils:
    @staticmethod
    def replace_container_config_placeholders(
        service_env_variables: Dict[str, Any],
        running_containers: Dict[str, RunningContainer],
        service_name: str,
        exposed_ports: List[str],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Utility method to replace placeholders in the service containers.
        Placeholders are usually of the form *${container_name.containerenv_variable}*.

        Args:
            service_env_variables (Dict[str, Any]): Dict of config environment variables
            running_containers Dict[str, RunningContainer]: Running container object
            service_name (str): service name as specified in the config
            exposed_ports (List[str]): container exposed ports

        Raises:
            ValueError: when a placeholder variable is not of the form service_name.variable_name
            AttributeError: When a service name could not be found in the list of services obtained from the
                            provided config file.

        Returns:
            Tuple[Dict[str, Any], List[str]]: A tuple of `env_config` and `exposed_ports`
        """
        pattern: str = "\\$\\{([^}]*)}"
        substituted_env_variables: Dict[str, Any] = copy(service_env_variables)
        modified_exposed_ports: List[str] = deepcopy(exposed_ports)
        cmpl = re.compile(pattern=pattern).findall
        for k, v in service_env_variables.items():
            if isinstance(v, str):
                replaced_variable: str = v
                for occurence in cmpl(v):
                    if len(str(occurence).split(".")) != 2:
                        raise ValueError
                    container_name, variable_name = str(occurence).split(".")
                    value = None
                    value, _exposed_ports = ContainerUtils._external_ports_variables(
                        running_containers,
                        service_name,
                        container_name,
                        variable_name,
                        modified_exposed_ports,
                    )
                    if _exposed_ports:
                        modified_exposed_ports = deepcopy(_exposed_ports)
                    replaced_variable = replaced_variable.replace(f"${{{occurence}}}", str(value))
                substituted_env_variables[k] = replaced_variable
        return substituted_env_variables, modified_exposed_ports

    @staticmethod
    def _get_free_host_port() -> str:
        """Get a free random port number from the container host

        Returns:
            str: port number
        """
        _socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        _socket.settimeout(2)
        _socket.bind(("", 0))
        _, port = _socket.getsockname()
        _socket.close()
        return port

    @staticmethod
    def _external_ports_variables(
        running_containers: Dict[str, RunningContainer],
        service_name: str,
        container_name: str,
        variable_name: str,
        exposed_ports: List[str] = list(),
    ) -> Tuple[Optional[str], List[str]]:
        value: Optional[str] = None
        _exposed_ports: List[str] = list()
        if container_name.lower() == SupportedPlaceholders.SELF_HOST or variable_name.lower() in [
            SupportedPlaceholders.CONTAINER_HOSTNAME,
            SupportedPlaceholders.EXTERNAL_PORT,
            SupportedPlaceholders.CONTAINER_HOST_ADDRESS,
        ]:
            if (
                container_name.lower() == SupportedPlaceholders.SELF_HOST
                and variable_name.lower() == SupportedPlaceholders.CONTAINER_HOSTNAME
            ):
                value = service_name
            elif (
                container_name.lower() != SupportedPlaceholders.SELF_HOST
                and variable_name.lower() == SupportedPlaceholders.CONTAINER_HOSTNAME
            ):
                value = container_name
            else:
                if variable_name.lower().startswith(SupportedPlaceholders.EXTERNAL_PORT):
                    value, _exposed_ports = ContainerUtils._external_port_variables(
                        variable_name, exposed_ports
                    )
                elif variable_name.lower() == SupportedPlaceholders.CONTAINER_HOST_ADDRESS:
                    value = socket.gethostbyname(socket.gethostname())
        else:
            value = running_containers[
                f"{container_name.lower()}"
            ].generic_container.container_environment_variables[f"{variable_name.upper()}"]

        return value, _exposed_ports

    @staticmethod
    def _external_port_variables(variable_name: str, exposed_ports: List[str]) -> Tuple[str, List[str]]:
        _exposed_ports: List[str] = deepcopy(exposed_ports)
        container_port: str = re.sub(SupportedPlaceholders.EXTERNAL_PORT + "_", "", variable_name)
        host_port: str = ContainerUtils._get_free_host_port()
        if container_port and container_port not in exposed_ports:
            raise AttributeError(
                f"self.hostport_{container_port} must be a valid supplied exposed_ports value!"
            )
        _exposed_ports.remove(container_port)
        _exposed_ports.append(f"{host_port}:{container_port}")
        value: str = str(host_port)
        return value, _exposed_ports
