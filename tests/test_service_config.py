from typing import List, Tuple
from docker import from_env
from docker.models.networks import Network
import pytest
from pydantic.error_wrappers import ValidationError
from config_fixtures import valid_container_config, config_with_missing_service_key, config_with_missing_attr
from docker_python.configs.service_config import Config
from docker_python.models.config import ITestConfig, RankedServices
from docker_python.models.network import NetworkConstants
from docker_python.containers.container_network import ContainerNetwork


def test_get_config_services_more_containers(valid_container_config):
    computed_services_instance = Config(test_services=ITestConfig(**valid_container_config))
    provided_service_config: ITestConfig = ITestConfig(**valid_container_config)

    assert isinstance(computed_services_instance.ranked_itest_config_services, RankedServices)
    assert computed_services_instance.ranked_itest_config_services.services
    assert len(provided_service_config.services) == len(
        computed_services_instance.ranked_itest_config_services.services
    )

    assert (
        computed_services_instance.ranked_itest_config_services.network.name
        == NetworkConstants.DEFAULT_NETWORK_MODE
    )

    _provided_ranks: List[Tuple[int, str]] = list()
    _computed_ranks: List[Tuple[int, str]] = list()
    for service in valid_container_config["services"]:
        _provided_ranks.append((service.get("spawn_rank"), service.get("name")))

    for service in computed_services_instance.ranked_itest_config_services.services:
        _computed_ranks.append((service[0], service[1]))

    assert _provided_ranks == _computed_ranks

    cnetwork = ContainerNetwork(
        docker_client=from_env(),
        network_name=computed_services_instance.ranked_itest_config_services.network.name,
    )

    assert cnetwork.network_name
    assert cnetwork.container_network
    assert isinstance(cnetwork.container_network, Network)

    with pytest.raises(AttributeError):
        ContainerNetwork(docker_client=from_env(), network_name="random_non_existing_network")


def test_container_attr_with_no_service(config_with_missing_service_key):
    with pytest.raises(expected_exception=ValidationError):
        Config(test_services=ITestConfig(**config_with_missing_service_key))


def test_container_missing_attr(config_with_missing_attr):
    with pytest.raises(expected_exception=ValidationError):
        Config(test_services=ITestConfig(**config_with_missing_attr))
