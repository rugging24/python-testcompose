from typing import Any, Dict
import yaml
import os
from testcompose.models.config import ITestConfig


class TestConfigParser:
    @classmethod
    def parse_config(cls, file_name: str) -> ITestConfig:
        """parses and verifies test yaml config file

        Args:
            file_name (str): absolutel path of the config file

        Raises:
            FileNotFoundError: when config file not present
            AttributeError: when config file is empty

        Returns:
            ITestConfig: A ITestConfig object with all named services in the config
        """
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Config file {file_name} does not exist!!")

        content: Dict[str, Any] = dict()
        with open(file_name, 'r') as fh:
            content = yaml.safe_load(fh)

        if not content:
            raise AttributeError(f"Config content can not be empty")

        test_services: ITestConfig = ITestConfig(**content)
        return test_services
