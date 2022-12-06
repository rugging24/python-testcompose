# QuickStart


Create a config object from a dict. See examples [here](https://github.com/rugging24/python-testcompose/blob/main/tests/containers_fixtures.py)

```python
from testcompose.configs.service_config import Config

run_config = Config(test_services=ConfigServices(**config))

```

Or from a yaml file. Example [here](https://github.com/rugging24/python-testcompose/blob/main/configurations/sample-config.yaml)

```python
import json
from typing import Any, Dict
from requests import Response, get
from testcompose.configs.service_config import Config
from testcompose.models.bootstrap.container_service import ContainerServices
from testcompose.models.container.running_container import RunningContainer
from testcompose.run_containers import RunContainers

config_services: ContainerServices = TestConfigParser.parse_config(file_name='some-config.yaml')
running_config: Config = Config(test_services=config_services)

```
The `some-config` file could contain something like the following:


```yaml
services:
  - name: database
    image: "postgres:13"
    command: ""
    environment:
      POSTGRES_USER: postgres
      POSTGRES_DB: postgres
      POSTGRES_PASSWORD: password
    exposed_ports:
      - 5432
    log_wait_parameters:
      log_line_regex: "database system is ready to accept connections"
      wait_timeout_ms: 30000
      poll_interval_ms: 2000
  - name: application
    image: "python:3.9"
    command: "/bin/bash -x /run_app.sh"
    environment:
      DB_URL: "${database.postgres_user}:${database.postgres_password}@${database.container_hostname}:5432/${database.postgres_db}"
    volumes:
      - host: "docker-test-files/run_app.sh"
        container: "/run_app.sh"
        mode: "ro"
        source: "filesystem"
      - host: "docker-test-files/app.py"
        container: "/app.py"
        mode: "ro"
        source: "filesystem"
    exposed_ports:
      - "8000"
    log_wait_parameters:
      log_line_regex: ".*Application startup complete.*"
      wait_timeout_ms: 45000
      poll_interval_ms: 2000
    http_wait_parameters:
      http_port: 8000
      response_status_code: 200
      end_point: "/ping"
      startup_delay_time_ms: 30000
      use_https": false
    depends_on:
      - database
```

Then let's run the containers and do some work

```python
with RunContainers(
        config_services=config_services,
        ranked_services=running_config.ranked_config_services,
) as runner:
    assert runner
    app_container_srv_name = "application"
    app_service: RunningContainer = runner.running_containers[app_container_srv_name]
    app_env_vars: Dict[str, Any] = app_service.config_environment_variables
    mapped_port = app_service.generic_container.get_exposed_port("8000")
    print(app_env_vars)
    app_host = app_service.generic_container.get_container_host_ip()
    assert app_env_vars
    assert mapped_port
    assert app_host
    response: Response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
    assert response
    assert response.status_code == 200
    assert response.text
    assert isinstance(json.loads(response.text), dict)

```

and Voila !!! you are all set !
