from testcompose.configs.config_templates import simple_app_or_db
from copy import deepcopy
from typing import Any, Dict, List
import yaml
import json


def remove_unwanted_keys(keys: List[str], template_dict: Dict[str, Any]):
    _template = deepcopy(template_dict)
    for k in keys:
        _template.pop(k)
    return _template


def generate_db_or_app_template() -> str:
    _template = remove_unwanted_keys(["http_wait_parameters", "depends_on"], simple_app_or_db())
    return yaml.dump(yaml.safe_load(json.dumps({"services": [_template]})))


def generate_app_and_db_template() -> str:
    _app = remove_unwanted_keys(["http_wait_parameters"], simple_app_or_db())
    _app["name"] = "app"
    _app["environment"] = {
        "DB_URL": "${db.db_user}:${db.db_password}@${db.container_hostname}:5432/${db.db_name}"
    }
    _app["depends_on"] = ["db"]
    _db = remove_unwanted_keys(["http_wait_parameters", "depends_on"], simple_app_or_db())
    _db["name"] = "db"
    _db["environment"] = {"DB_USER": "user", "DB_PASSWORD": "very-secret", "DB_NAME": "some_db_name"}
    _template: Dict[str, Any] = {"services": [_app, _db]}
    return yaml.dump(yaml.safe_load(json.dumps(_template)))


def generate_broker_template():
    pass
