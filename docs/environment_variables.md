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

- **`container_host_address`**: This special variable exposes the hostname of the contianer host. This is mostly uuseful when an external script needs to interact with the running docker images. It is particularly useful if the host has a different hostname other than `localhost`.
- **`external_port`**: Sometimes is is necessary to fix the host port to the running container. Even though this is greatly discouraged as it is advisable to allow `TestContainers` use random host port; some situations i.e for running Kafka docker images might require one to know the host port prior to starting the docker image. This is usually of the format `external_port_PORT_NUMBER`. As an example, assuming one would like to map the internal docker port 9092 with a random host port at container startup, one should specify this variable as `external_port_9092`.

`Testcompose` in this case assigns a random available port to be mapped with the port `9092`.
- **`container_hostname`**: This is mainly the hostname of the docker image as seen within the created docker network. Usually, this is assigned the service name provided in the config.
- **`self`**: This is a keyword use to mean the `current` image itself. E.g to specify the hostname of a service in its environment variable, one could write `http://${self.container_hostname}/ping` which will replace the plaeholder variable at startup.

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
      APP2_KEY_1: "http://${app1.container_hostname}/${app1.somekey_app1_3}:5592",
      APP2_KEY_2: a
    exposed_ports:
      - 4450
    depends_on:
      - app1
```

And this will be translated as `http://${app1.docker_python_internal_host}/${app1.somekey_app1_3}:5592` -> `http://app1-runtimehostname/localtest:5592`. Where `app1-runtimehostname` is determined at runtime.


The variable combination of with the keywords might vary depending on what usage is intended. One could use a combination of `self` with all the other specifal variables e.g `${self.container_hostname}`, `${self.container_host_address}` and so on. As well as using it in a different form with `self` replaced by the name of a reference service. E.g for the config above, one could specify `${app1.container_hostname}` which will be replaced with `app1` since the service name is always used as the container hostname.
