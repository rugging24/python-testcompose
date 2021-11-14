import pytest


@pytest.fixture(scope="module")
def valid_container_config():
      return {
      "network": {},
      "services": [
            {
                  "name": "database",
                  "image": "postgres:13",
                  "auto_remove": True,
                  "command": "",
                  "environment": {
                        "POSTGRES_USER": "postgres",
                        "POSTGRES_DB": "postgres",
                        "POSTGRES_PASSWORD": "password"
                  },
                  "exposed_ports": [
                        5432
                  ],
                  "volumes": [
                        {
                              "host": "itest_db_volume",
                              "container": "/var/lib/postgresql/data",
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
                  "name": "application",
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
                              "container": "/app",
                              "mode": "ro"
                        }
                  ],
                  "http_wait_parameters": {
                        "http_port": 8081,
                        "response_status_code": 200
                  },
                  "spawn_rank": 1,
                  "depends_on": [
                        "database"
                  ]
            },
            {
                  "name": "application2",
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
                              "container": "/app",
                              "mode": "ro"
                        }
                  ],
                  "http_wait_parameters": {
                        "http_port": 8081,
                        "response_status_code": 200
                  },
                  "spawn_rank": 2,
                  "depends_on": [
                        "database",
                        "application"
                  ]
            }
      ]
}

@pytest.fixture
def config_with_missing_service_key():
      return {
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
            }
      }

@pytest.fixture(scope="module")
def config_with_missing_attr():
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
                  }
            }
      ]
}