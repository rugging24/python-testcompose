# QuickStart


Create a config object from a dict. See examples [here](https://github.com/rugging24/python-testcompose/blob/main/tests/containers_fixtures.py)

```python
from testcompose.configs.service_config import Config

run_config = Config(test_services=ConfigServices(**config))

```

Or from a yaml file. Example [here](https://github.com/rugging24/python-testcompose/blob/main/configurations/sample-config.yaml)

```python
from testcompose.configs.parse_config import TestConfigParser
from testcompose.configs.service_config import Config
from testcompose.models.config.config_services import ConfigServices

config = TestConfigParser.parse_config(file_name='some-config.yaml')
run_config = Config(test_services=ConfigServices(**config))

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
    app_env_vars = app_service.config_environment_variables
    mapped_port = app_service.generic_container.get_exposed_port("8000")
    print(app_env_vars)
    app_host = app_service.generic_container.get_container_host_ip()
    assert app_env_vars
    assert mapped_port
    assert app_host
    response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
    assert response
    assert response.status_code == 200
    assert response.text
    assert isinstance(json.loads(response.text), dict)

```

and Voila !!! you are all set !
