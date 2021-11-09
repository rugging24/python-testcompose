import json
from typing import Any, Dict, Tuple
from io import BytesIO
import tarfile
from requests import get
from docker_python.configs.service_config import Config
from docker_python.models.config import (
      Services
)
from docker_python.run_containers import RunContainers
from run_containers_fixtures import (
      db_and_app_containers,
      broker_app_and_db_containers
)

# def test_db_and_app_containers(db_and_app_containers):
#       running_config = Config()
#       running_config.get_container_spawn_precedence(test_services=Services(**db_and_app_containers))
#       assert running_config.ranked_itest_config_services
#       with RunContainers(
#             services=running_config.ranked_itest_config_services,
#       ) as runner:
#             assert runner.containers
#             app_container_srv_name = "application"
#             app_env_vars= runner.extra_envs[app_container_srv_name]
#             mapped_port = app_env_vars.get("DOCKER_PYTHON_MAPPED_PORTS", {}).get('8000')
#             print(app_env_vars)
#             app_host = app_env_vars.get('DOCKER_PYTHON_EXTERNAL_HOST')
#             assert app_env_vars
#             assert mapped_port
#             assert app_host
#             response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
#             print(response)
#             assert response
#             assert response.status_code == 200
#             assert response.text
#             assert isinstance(json.loads(response.text), dict)

def test_broker_app_and_db_containers(broker_app_and_db_containers) -> None:
      running_config = Config()
      running_config.get_container_spawn_precedence(test_services=Services(**broker_app_and_db_containers))
      assert running_config.ranked_itest_config_services
      with RunContainers(services=running_config.ranked_itest_config_services) as runner:
            assert runner.containers