from copy import deepcopy
from typing import Any, Dict, List

from testcompose.configs.config_templates import simple_app_or_db, simple_broker


class GenerateConfigTemplate:
    def _remove_keys(self, keys: List[str], template_dict: Dict[str, Any]):
        _template = deepcopy(template_dict)
        for k in keys:
            _template.pop(k)
        return _template

    def _app_db_template(self) -> Dict[str, List[Dict[str, Any]]]:
        _app = self._remove_keys(["http_wait_parameters"], simple_app_or_db())
        _app["name"] = "app"
        _app["environment"] = {
            "DB_URL": "${db.db_user}:${db.db_password}@${db.container_hostname}:5432/${db.db_name}"  # noqa: E501
        }
        _app["depends_on"] = ["db"]
        _db = self._remove_keys(["http_wait_parameters", "depends_on"], simple_app_or_db())  # noqa: E501
        _db["name"] = "db"
        _db["environment"] = {"DB_USER": "user", "DB_PASSWORD": "very-secret", "DB_NAME": "some_db_name"}  # noqa: E501
        return {"services": [_app, _db]}

    def app_template(self) -> Dict[str, Any]:
        _template = self._remove_keys(["depends_on"], simple_app_or_db())
        _template['name'] = 'app'
        return {"services": [_template]}

    def db_template(self) -> Dict[str, Any]:
        _template = self._remove_keys(["http_wait_parameters", "depends_on"], simple_app_or_db())  # noqa: E501
        _template['name'] = 'db'
        return {"services": [_template]}

    def broker_template(self) -> Dict[str, Any]:
        return simple_broker()

    def app_db_template(self) -> Dict[str, Any]:
        return self._app_db_template()

    def app_broker_db_template(self) -> Dict[str, Any]:
        _services: List[Dict[str, Any]] = list()
        for x in self._app_db_template()['services']:
            app = deepcopy(x)
            if x.get('name') == 'app':
                app["depends_on"].append("broker")
            _services.append(app)

        _broker_template: Dict[str, Any] = simple_broker()
        _services.extend(_broker_template['services'])
        _broker_template['services'] = _services
        return _broker_template

    def app_broker_template(self) -> Dict[str, Any]:
        _app_template: Dict[str, Any] = simple_app_or_db()
        _app_template['depends_on'] = ['broker']
        _app_template['name'] = 'app'
        _broker_template: Dict[str, Any] = simple_broker()
        _services: List[Dict[str, Any]] = _broker_template['services']
        _services.append(_app_template)
        _broker_template['services'] = _services
        return _broker_template

    def broker_db_template(self) -> Dict[str, Any]:
        _db_template: Dict[str, Any] = simple_app_or_db()
        _db_template['name'] = 'db'
        _broker_template: Dict[str, Any] = simple_broker()
        _services: List[Dict[str, Any]] = _broker_template['services']
        _services.append(_db_template)
        _broker_template['services'] = _services
        return _broker_template
