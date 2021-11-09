import re
from copy import copy
from typing import Any, Dict
from docker_python.models.container import RunningContainer

class Utils:
    @staticmethod
    def replace_pace_config_placeholders(
        env_config: Dict[str, Any], 
        dependency_mapping: Dict[str, int],
        running_containers: RunningContainer
    ) -> Dict[str, Any]:
        pattern = "\\$\\{([^}]*)}"
        _env_config: Dict[str, Any] = copy(env_config)
        cmpl = re.compile(pattern=pattern).findall
        for k, v in env_config.items():
            if isinstance(v, str):
                replaced_varoable = v
                print(cmpl(v))
                for occurence in cmpl(v):
                    if len(str(occurence).split(".")) != 2:
                        raise ValueError
                    container_name, variable_name = str(occurence).split(".")
                    if container_name.lower() not in dependency_mapping:
                        raise AttributeError
                    _value = None
                    if variable_name.lower().startswith("docker_python"):
                        _value = env_config[f"{variable_name.upper()}_{container_name.upper()}"]
                    else:
                        _value = running_containers.containers[f"{container_name.lower()}"].env[f"{variable_name.upper()}"]
                    replaced_varoable = replaced_varoable.replace(f"${{{occurence}}}", str(_value))
                _env_config[k] = replaced_varoable
        return _env_config