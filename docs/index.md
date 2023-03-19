<p align="center" style="margin: 0 0 10px">
  <img width="350" height="208" src="images/testcompose.png" alt='Testcompose'>
</p>

<h1 align="center" style="font-size: 3rem; margin: -15px 0">
Testcompose
</h1>

---

**Testcompose** provides an easy way of using docker containers for functional and integration testing. It allows for combination of more than one containers and allows for interactions with these containers from your test code without having to write extra scripts for such interactions. I.e providing a docker compose kind of functionality with the extra benefit of being able to fully control the containers from test codes.

This is inspired by the [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/index.html#) project and goes further to add a few additional functionalities to improve software integration testing while allowing the engineer to control every aspect of the test.

---

Install testcompose using pip:

```shell
$ pip install testcompose
```

testcompose requires Python 3.7+.

```shell
# Testcompose include a cli utility to help create a quickstart config file that should be update to suit the needs of the user.
# Create a config file by running the command

testcompose generate-template --help   # shows the help and exit.

# To generate template config for an app and a db combination, run the command

testcompose generate-template --component db --component app

# The above command ouputs to stdout. To output to a file, include a filepath as below

testcompose generate-template --component db --component app --template-file some-valid-file-location.yaml

```

A sample of the config file is represented below:

```yaml
services:
  - name: db1
    image: "postgres:13"
    command: ""
    environment:
      POSTGRES_USER: postgres
      POSTGRES_DB: postgres
      POSTGRES_PASSWORD: password
    exposed_ports:
      - 5432
    volumes:
      - host: "data_volume"
        container: "/data"
        mode: "rw"
        source: "dockervolume" # possible values are `dockervolume` or `filesystem`
    log_wait_parameters:
      log_line_regex: "database system is ready to accept connections"
      wait_timeout_ms: 30
      poll_interval_ms: 2
```

Verify it as follows:

```python
from testcompose.parse_config import TestConfigParser
from testcompose.configs.service_config import Config
from testcompose.run_containers import RunContainers
from testcompose.models.config.config_services import ConfigServices, Service

my_test_service: ConfigServices = TestConfigParser.parse_config(
    file_name='some-file-name'
)
my_config: Config =  Config(test_services=my_test_service)

with RunContainers(
        services=running_config.ranked_itest_config_services
) as runner:
    # Interract with the running containers

    assert runner.running_containers

    # Use some special parameters of the running containers

    app_container = runner.running_containers["app_container_config_name"].config_environment_variables

    # Get the host port a certain exposed container port is mapped to
    mapped_port = app_container.generic_container.get_exposed_port("8000")

    # where `port` is the exposed port of the container


```


## Documentation

For a run-through of all the basics, head over to the [QuickStart](quickstart.md).

The [Developer Interface](api.md) provides a comprehensive API reference.
