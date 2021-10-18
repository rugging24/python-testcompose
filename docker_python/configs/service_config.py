
import os
from copy import deepcopy
import yaml
from typing import Dict, Union
from docker_python.models.config import Services, ItestConfigMapper
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)


class Config:
    def __init__(self, config_file) -> None:
        self._config_file = config_file

    def get_config_services(self) -> Dict[int, ItestConfigMapper]:
        if not os.path.exists(self._config_file):
            logger.error("Config file %s not Found!", self._config_file)
            raise FileNotFoundError
        config_services: Dict[int, ItestConfigMapper] = dict()
        config: Union[Services, None] = None

        with open(self._config_file, 'r') as fh:
            content = yaml.safe_load(fh)
            config = Services(**content)
        if not config:
            logger.error("Config file (%s) content can not be empty", self._config_file)
            raise AttributeError
        config_services = self.get_container_spawn_precedence(config)
        return config_services
    
    def get_container_spawn_precedence(self, config: Services) -> Dict[int, ItestConfigMapper]:
        _config_services: Dict[int, ItestConfigMapper] = dict()
        for service in config.services:
            _config_services.update({service.spawn_rank: service})
        if not _config_services:
            logger.error("No services were found in config file: %s", self._config_file)
            raise ValueError
        _ranks = list(_config_services.keys())
        _ranks.sort()
        config_services = {
            r: _config_services[r]
            for r in _ranks
        }
        
        return config_services
            
