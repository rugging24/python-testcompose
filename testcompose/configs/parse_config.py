from typing import Any, Dict
import yaml
import os
from testcompose.models.config.config_services import ConfigServices, Service


class TestConfigParser:
    @classmethod
    def parse_config(cls, file_name: str) -> ConfigServices:
        """parses and verifies test yaml config file

        Args:
            file_name (str): absolutel path of the config file

        Raises:
            FileNotFoundError: when config file not present
            AttributeError: when config file is empty

        Returns:
            ConfigServices: A ConfigServices object with all named services in the config
        """
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Config file {file_name} does not exist!!")

        contents: Dict[str, Any] = dict()
        with open(file_name, 'r') as fh:
            contents = yaml.safe_load(fh)

        if not contents:
            raise AttributeError(f"Config content can not be empty")

        services: Dict[str, Service] = dict()
        for service in contents["services"]:
            services.update({service["name"]: Service(**service)})

        test_services: ConfigServices = ConfigServices(services=services)
        return test_services
