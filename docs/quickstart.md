# QuickStart


Create a config object from a dict. See examples [here](https://github.com/rugging24/python-testcompose/blob/main/tests/containers_fixtures.py)

```python
from testcompose.configs.service_config import Config

run_config = Config(test_services=ITestConfig(**config))
```

Or from a yaml file. Example [here](https://github.com/rugging24/python-testcompose/blob/main/configurations/sample-config.yaml)

```python
from testcompose.configs.parse_config import TestConfigParser

config = TestConfigParser.parse_config(file_name='some-config.yaml')
run_config = Config(test_services=ITestConfig(**config))
```

Then let's run the containers and do some work
```python
with RunContainers(services=run_config.ranked_itest_config_services) as runner:
    assert runner.containers
    # do or pretend to do some work
    app_container_srv_name = "application"
    app_env_vars = runner.extra_envs[app_container_srv_name]
    mapped_port = app_env_vars.get("DOCKER_PYTHON_MAPPED_PORTS", {}).get("8000")
    app_host = app_env_vars.get("DOCKER_PYTHON_EXTERNAL_HOST")
    response = get(url=f"http://{app_host}:{int(mapped_port)}/version")
    print(response)
```

and Voila !!! you are all set !
