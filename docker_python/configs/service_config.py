from copy import deepcopy
from typing import Dict, Any
from docker_python.models.config import Services, ItestConfigMapper, RankedServices, RankedServiceKey
from testcontainers.core.utils import setup_logger

logger = setup_logger(__name__)


class Config:
    def __init__(self, config_content: Dict[str, Any]) -> None:
        self._config_content = deepcopy(config_content)

    def get_config_services(self) -> RankedServices:
        config: Services = Services(**self._config_content)
        config_services: RankedServices = self.get_container_spawn_precedence(config)
        return config_services
    
    def get_container_spawn_precedence(self, config: Services) -> RankedServices:
        _config_services: Dict[int, ItestConfigMapper] = dict()
        for service in config.services:
            _config_services.update({service.spawn_rank: service})
        if not _config_services:
            logger.error("No services were found in config file: %s", self._config_content)
            raise ValueError
        # _ranks = list(_config_services.keys())
        # _ranks.sort()
        # config_services = dict()
        # for r in _ranks:
        #     config_services.update({"rank": r, "service": _config_services[r]})
        
        return RankedServices(**{RankedServiceKey.SERVICES: _config_services})
            
