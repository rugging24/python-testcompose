# Environment Variables

These are generally variables exposed on a running container as environment variables. The can be specified in the configuration as:

```yaml
...
environment:
  SOMEKEY_1: some_value_1
  SOMEKEY_2: some_value_2
  SOMEKEY_3: some_value_3
...
```

The above variables `SOMEKEY_1`, `SOMEKEY_2` and `SOMEKEY_3` will be available from within the container as environment variables.
Place holder variables from another container can also be used in a container as environment variables as long as the container looking to expose such variables depends on the other contnainer. i.e

```yaml
services:
  - name: app1
    image: "node"
    auto_remove: True
    command: ""
    environment:
      SOMEKEY_APP1_1: localhost
      SOMEKEY_APP1_2: postgres
      SOMEKEY_APP1_3: localtest
    exposed_ports:
      - 5432
  - name: app2
    image: "node"
    auto_remove: True
    command: ""
    environment:
      APP2_KEY_1: "http://${app1.somekey_app1_1}-${app1.somekey_app1_2}/${app1.somekey_app1_3}:5592",
      APP2_KEY_2: a
    exposed_ports:
      - 4450
    depends_on:
      - app1
```

The above placeholder variable `http://${app1.somekey_app1_1}:${app1.somekey_app1_2}/${app1.somekey_app1_3}:5592` of `app2` will be translated at runtime as `http://localhost-postgres/localtest:5592`. A primary requirement of this is that `app2` depends on `app1`!.


## Extra Environment Variables

The following extra environment variables are included in all running containers regardless of whether they container environment variables of their own or not. These variables are:

- **`DOCKER_PYTHON_EXTERNAL_HOST`**: This special variable exposes the hostname of the contianer host. This is of two variations `DOCKER_PYTHON_EXTERNAL_HOST_SERVICE_NAME` shows the hostname of the container host that a certain container depends on. i.e if container `A` with service name `SERVICE_NAME_A` deppends on container `B` with service name `SERVICE_NAME_B`, container `A` will container the extra variable `DOCKER_PYTHON_EXTERNAL_HOST_SERVICE_NAME_B` and another for itself named `DOCKER_PYTHON_EXTERNAL_HOST`. In most cases these two values will be the same, except for cases where both containers are running on separate hosts.
- **`DOCKER_PYTHON_INTERNAL_HOST`**: This variable adds the container hostname as an environment variable. This value is usually derived after a container is successfully started. It is useful especially in situation where another container depending on this container requires this containers hostname for a given operation. I.e for two containers `A` and `B` with service names `SERVICE_NAME_A` and `SERVICE_NAME_B` respectively with `A` depending on `B`, `A` will have an extra environment variable `DOCKER_PYTHON_INTERNAL_HOST_SERVICE_NAME_B` so as to be able to reference the service running in container `B`.
- **`DOCKER_PYTHON_MAPPED_PORTS`**: This follows the same principle as the `DOCKER_PYTHON_EXTERNAL_HOST` where for two containers `A` and `B` with service names `SERVICE_NAME_A` and `SERVICE_NAME_B` respectively with `A` depending on `B`. Then the container `A` will have the following extra environment variables `DOCKER_PYTHON_MAPPED_PORTS_SERVICE_NAME_B` and `DOCKER_PYTHON_MAPPED_PORTS`. While container `B` will have only `DOCKER_PYTHON_MAPPED_PORTS`.

To use this set of variables, the `yaml` config above could be extended as shown:

```yaml
services:
  - name: app1
    image: "node"
    auto_remove: True
    command: ""
    environment:
      SOMEKEY_APP1_1: localhost
      SOMEKEY_APP1_2: postgres
      SOMEKEY_APP1_3: localtest
    exposed_ports:
      - 5432
  - name: app2
    image: "node"
    auto_remove: True
    command: ""
    environment:
      APP2_KEY_1: "http://${app1.docker_python_internal_host}/${app1.somekey_app1_3}:5592",
      APP2_KEY_2: a
    exposed_ports:
      - 4450
    depends_on:
      - app1
```

And this will be translated as `http://${app1.docker_python_internal_host}/${app1.somekey_app1_3}:5592` -> `http://app1-runtimehostname/localtest:5592`. Where `app1-runtimehostname` is determined at runtime.


## Using **`self`** Variables

Sometimes, a given service running in a container will require variables that can only be set at service start time. i.e the container must already be running to be able to obtain the real value of such variable. These set of variables are referred to as the `self` container variables. They can only be used with the following conditions:

- Only for the current container internal usage. This can not be referenced by another container which depends on this container.
- This only allows for the variables `hostname` and `host ports` denoted as `self.hostname` and `self.hostport_xxxx` respectively. Note that the host port variable are for services whose attached host ports are only determined ones the service is started but is required as part of the configuration.

To use the `self` variables, the `yaml` config above could be extended as shown:

```yaml
services:
  - name: app1
    image: "node"
    auto_remove: True
    command: ""
    environment:
      SOMEKEY_APP1_1: localhost
      SOMEKEY_APP1_2: postgres
      SOMEKEY_APP1_3: localtest
    exposed_ports:
      - 5432
  - name: app2
    image: "node"
    auto_remove: True
    command: ""
    environment:
      APP2_KEY_1: "http://${self.hostname}/${app1.somekey_app1_3}:${self.hostport_4450}",
      APP2_KEY_2: a
    exposed_ports:
      - 4450
    depends_on:
      - app1
```

The `self.hostname` and `self.hostport_4450` replacement can only be determined at runtime. Note the `4450` with the host variable. This is because only host port attached to a container exposed port can be deduced. Using a none exposed port for this will result in an error.

**Note:** Refering to containers by their `hostnames` only works in environments where the container network is not the default `bridge` network. i.e One must use an existing docker network or create one by specifying the `use_random_network` option in the config.
