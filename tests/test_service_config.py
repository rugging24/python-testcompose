from docker import from_env  # type: ignore
import pytest
from pydantic.error_wrappers import ValidationError
from .config_fixtures import valid_container_config, config_with_missing_service_key, config_with_missing_attr
from testcompose.configs.parse_config import TestConfigParser
from testcompose.configs.service_config import Config
from testcompose.models.bootstrap.container_service import ContainerServices, RankedContainerServices
from testcompose.containers.container_network import ContainerNetwork
from unittest import mock
import json


def test_get_config_services_more_containers(valid_container_config):
    config_services: ContainerServices
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(valid_container_config))):
        with open('some_file_name') as f2:
            config_services = TestConfigParser.parse_config(file_name=f2.name)

    assert config_services
    assert isinstance(config_services, ContainerServices)
    test_services = Config(test_services=config_services)

    assert test_services

    computed_services = list(test_services.ranked_config_services.ranked_services.values())
    provided_services = [x["name"] for x in valid_container_config.get("services")]

    assert isinstance(test_services.ranked_config_services, RankedContainerServices)
    assert test_services.ranked_config_services.ranked_services
    assert len(computed_services) == len(provided_services)
    assert list(set(computed_services).difference(provided_services)) == list()

    network_name: str = "random_non_existing_network"
    container_network: ContainerNetwork = ContainerNetwork(
        docker_client=from_env(), network_name=network_name
    )
    assert container_network.name == network_name


def test_container_attr_with_no_service(config_with_missing_service_key):
    with pytest.raises(expected_exception=ValidationError):
        Config(test_services=ContainerServices(**config_with_missing_service_key))


def test_container_missing_attr(config_with_missing_attr):
    with pytest.raises(expected_exception=ValidationError):
        Config(test_services=ContainerServices(**config_with_missing_attr))
