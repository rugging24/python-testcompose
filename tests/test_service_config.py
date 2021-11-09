from typing import List, Tuple
import pytest
from unittest.mock import patch
from pydantic.error_wrappers import ValidationError
from docker_python.configs.service_config import Config
from docker_python.models.config import (
      Services, 
      RankedServices
)
from config_fixtures import (
      valid_container_config,
      config_with_missing_service_key,
      config_with_missing_attr
)


def test_get_config_services_more_containers(valid_container_config):
      computed_services_instance = Config()
      provided_services: Services = Services(**valid_container_config)
      computed_services_instance.get_container_spawn_precedence(test_services=provided_services)

      assert isinstance(computed_services_instance.ranked_itest_config_services, RankedServices)
      assert computed_services_instance.ranked_itest_config_services.services
      assert len(provided_services.services) == len(computed_services_instance.ranked_itest_config_services.services)

      _provided_ranks: List[Tuple[int, str]] = list()
      _computed_ranks: List[Tuple[int, str]] = list()
      for service in valid_container_config["services"]:
            _provided_ranks.append((service.get("spawn_rank"), service.get("name")))

      for service in computed_services_instance.ranked_itest_config_services.services:
            _computed_ranks.append((service[0], service[1]))
      
      assert _provided_ranks == _computed_ranks

def test_container_attr_with_no_service(config_with_missing_service_key):
      with pytest.raises(expected_exception=ValidationError):
            Config().get_container_spawn_precedence(test_services=Services(**config_with_missing_service_key))

def test_container_missing_attr(config_with_missing_attr):
      with pytest.raises(expected_exception=ValidationError):
            Config().get_container_spawn_precedence(test_services=Services(**config_with_missing_attr))