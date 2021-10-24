import os
from typing import Any, Dict
import yaml
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)

class Utility:
      @staticmethod
      def parse_yaml_config(config_file: str) -> Dict[str, Any]:
            if not os.path.exists(config_file):
                  logger.error("Config file %s not Found!", config_file)
                  raise FileNotFoundError
            
            content = dict()
            with open(config_file, 'r') as fh:
                  content = yaml.safe_load(fh)

            if not content:
                  logger.error("Config file (%s) content can not be empty", config_file)
                  raise AttributeError
            return content