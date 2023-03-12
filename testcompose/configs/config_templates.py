from typing import Any, Dict


def simple_app_or_db() -> Dict[str, Any]:
    _template: Dict[str, Any] = {
        "name": "service-name",
        "image": "some-valid-image-name",
        "auto_remove": True,
        "command": "",
        "environment": {
            "ENV_VARIABLE_1": "VALUE_1",
            "ENV_VARIABLE_2": "VALUE_2",
            "ENV_VARIABLE_N": "...VALUE_N",
        },
        "volumes": [
            {"host": "/some-valid-location-on-host", "container": "/data", "mode": "rw"},
            {
                "host": "/another-valid-location-on-host",
                "container": "/data2",
                "mode": "ro",  # This is one of rw|ro
            },
        ],
        "log_wait_parameters": {
            "log_line_regex": ".*Some regex to check for in the container log.*",
            "wait_timeout": 30.0,
            "poll_interval": 1,
        },
        "http_wait_parameters": {
            "http_port": "8080",
            "response_status_code": 200,
            "end_point": "/ping",
            "startup_delay_time": 20,
        },
        "depends_on": [],
    }

    return _template


def sample_broker():
    pass
