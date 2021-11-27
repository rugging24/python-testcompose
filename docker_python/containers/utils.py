import re
import socket
from copy import copy, deepcopy
from typing import Any, Dict, List, Optional, Tuple
from docker_python.models.container import RunningContainer

class ContainerUtils:
    @staticmethod
    def replace_container_config_placeholders(
        env_config: Dict[str, Any], 
        dependency_mapping: Dict[str, int],
        running_containers: RunningContainer,
        unique_container_label: str,
        service_name: str,
        exposed_ports: List[str]
    ) -> Tuple[Dict[str, Any], List[str]]:
        pattern = "\\$\\{([^}]*)}"
        _env_config: Dict[str, Any] = copy(env_config)
        _exposed_ports = deepcopy(exposed_ports)
        cmpl = re.compile(pattern=pattern).findall
        for k, v in env_config.items():
            if isinstance(v, str):
                replaced_varoable = v
                for occurence in cmpl(v):
                    if len(str(occurence).split(".")) != 2:
                        raise ValueError
                    container_name, variable_name = str(occurence).split(".")
                    if container_name.lower() not in dependency_mapping and \
                        container_name.lower() != "self":
                        raise AttributeError
                    _value = None
                    if container_name.lower() != "self":
                        if variable_name.lower().startswith("docker_python"):
                            _value = env_config[f"{variable_name.upper()}_{container_name.upper()}"]
                        else:
                            _value = running_containers.containers[f"{container_name.lower()}"].env[f"{variable_name.upper()}"]
                    else:
                        if variable_name.lower() == "hostname":
                            _value = f"{unique_container_label}_{service_name}"
                        elif variable_name.lower().startswith("hostport_"):
                            container_port = re.sub("hostport_", "", variable_name)
                            host_port = ContainerUtils._get_assigned_free_port(_exposed_ports, container_port)
                            if not host_port:
                                host_port = ContainerUtils.get_free_host_port()
                                if container_port and container_port not in _exposed_ports:
                                    raise AttributeError(f"self.hostport_{container_port} must be a valid supplied exposed_ports value!")
                                _exposed_ports.remove(container_port)
                                _exposed_ports.append(f"{host_port}:{container_port}")
                            _value = str(host_port)
                        else:
                            raise AttributeError("Container self reference only support hostname and hostport. i.e self.hostname|self.hostport_1234")
                    replaced_varoable = replaced_varoable.replace(f"${{{occurence}}}", str(_value))
                _env_config[k] = replaced_varoable
        return _env_config, _exposed_ports
    
    @staticmethod
    def get_free_host_port() -> str:
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.settimeout(2)
        s.bind(('', 0))
        addr, port = s.getsockname()
        s.close()
        return port
    
    @staticmethod
    def _get_assigned_free_port(modified_exposed_ports: List[str], container_port: str) -> Optional[str]:
        host_port: Optional[str] = None
        count = set([
            x for x in modified_exposed_ports if x.endswith(f":{container_port}")
        ])
        if count:
            host_port = str(list(count)[0]).split(":")[0]
        
        return host_port