<h1 align="center" style="font-size: 3rem; margin: -15px 0">
Testcompose
</h1>



<p align="center" style="margin: 30px 0 10px">
  <img width="350" height="208" src="docs/images/testcompose.png" alt='Testcompose'>
</p>

<p align="center"><strong>Testcompose</strong> <em>- A clean and better way to test your Python containerized applications.</em></p>



![PyPI - Python Version](https://img.shields.io/pypi/pyversions/testcompose)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/testcompose)
![PyPI](https://img.shields.io/pypi/v/testcompose)
![PyPI - Downloads](https://img.shields.io/pypi/dm/testcompose)
[![Tests](https://github.com/rugging24/python-testcompose/workflows/RunningTests/badge.svg)](https://github.com/rugging24/python-testcompose/blob/main/.github/workflows/tests.yaml)


---
**Testcompose** provides an easy way of using docker containers for functional and integration testing. It allows for combination of more than one containers and allows for interactions with these containers from your test code without having to write extra scripts for such interactions. I.e providing a docker compose kind of functionality with the extra benefit of being able to fully control the containers from test codes.

This is inspired by the [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/index.html#) project and goes further to add a few additional functionalities to improve software integration testing while allowing the engineer to control every aspect of the test.

---

Install testcompose using pip:

```shell
$ pip install testcompose
```

testcompose requires Python 3.7+.

Using a config file. See the [Quickstart](https://github.com/rugging24/python-testcompose/blob/main/docs/quickstart.md) for other options

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

Verify it as follows:

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


## Documentation

[Quickstart](https://github.com/rugging24/python-testcompose/blob/main/docs/quickstart.md)

[Special-Variables](https://github.com/rugging24/python-testcompose/blob/main/docs/environment_variables.md)

[Full-Doc](https://rugging24.github.io/python-testcompose/)
