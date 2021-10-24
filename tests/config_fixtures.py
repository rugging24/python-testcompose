import pytest


@pytest.fixture(scope="module")
def more_containers():
      return {
      "services": [
            {
                  "name": "db1",
                  "image": "postgres:13",
                  "auto_remove": True,
                  "command": "",
                  "environment": {
                        "POSTGRES_USER": "postgres",
                        "POSTGRES_DB": "postgres",
                        "POSTGRES_PASSWORD": "a"
                  },
                  "exposed_ports": [
                        5432
                  ],
                  "volumes": [
                        {
                              "host": "/data",
                              "container": "/data",
                              "mode": "rw"
                        }
                  ],
                  "log_wait_parameters": {
                        "log_line_regex": "database system is ready to accept connections",
                        "wait_timeout": 30,
                        "poll_interval": 2
                  },
                  "spawn_rank": 0
            },
            {
                  "name": "app1",
                  "image": "node:13",
                  "auto_remove": False,
                  "command": "ls -l",
                  "exposed_ports": [
                        67543,
                        54432
                  ],
                  "volumes": [
                        {
                              "host": "/data",
                              "container": "/data",
                              "mode": "rw"
                        },
                        {
                              "host": "/data2",
                              "container": "/data2",
                              "mode": "ro"
                        }
                  ],
                  "http_wait_parameters": {
                        "http_port": 8081,
                        "response_status_code": 200
                  },
                  "spawn_rank": 1
            }
      ]
}