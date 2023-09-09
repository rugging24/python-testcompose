import os
from typing import Any, Dict

import yaml

from testcompose.models.bootstrap.container_service import ContainerService, ContainerServices  # noqa: E501


class TestConfigParser:
    @classmethod
    def parse_config(cls, file_name: str) -> ContainerServices:
        """parses and verifies test yaml config file

        Args:
            file_name (str): absolute path of the config file

        Raises:
            FileNotFoundError: when config file not present
            AttributeError: when config file is empty

        Returns:
            ConfigServices: A ConfigServices object with all named services in the config
        """  # noqa: E501
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Config file {file_name} does not exist!!")

        contents: Dict[str, Any] = dict()
        with open(file_name, 'r') as fh:
            contents = yaml.safe_load(fh)

        if not contents:
            raise AttributeError("Config content can not be empty")

        services: Dict[str, ContainerService] = dict()
        for service in contents["services"]:
            services.update({service["name"]: ContainerService(**service)})

        container_services: ContainerServices = ContainerServices(services=services)
        return container_services
