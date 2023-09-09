from copy import deepcopy
from logging import Logger
from typing import Dict, List

from testcompose.log_setup import stream_logger
from testcompose.models.bootstrap.container_service import (  # noqa: E501
    ContainerService,
    ContainerServices,
    RankedContainerServices,
)

logger: Logger = stream_logger(__name__)


class Config:
    """This class consumes the model created from a config file.
    This is an important class that sets the precedence of how the
    different containers are to be started and stopped. Usually, the
    precedence are set correctly if the `depends_on` parameter of the
    config is set. Cyclic dependency will fail the test before it starts.

    Args:
        test_services (ConfigServices): model resulting from a parsed configuration file.
    """  # noqa: E501

    def __init__(self, test_services: ContainerServices) -> None:
        self._rank_test_services(test_services)

    @property
    def ranked_config_services(self) -> RankedContainerServices:
        """Object containing the ordered services from the config

        Returns:
            RankedServices: ranked container services
        """
        return self._ranked_it_services

    @ranked_config_services.setter
    def ranked_config_services(self, ranked_services: RankedContainerServices) -> None:
        self._ranked_it_services: RankedContainerServices = ranked_services

    def _rank_test_services(self, test_services: ContainerServices) -> None:
        """
        Args:
            test_services (ConfigServices): model resulting from a parsed configuration file.

        Raises:
            ValueError: raised if test_services is `null`
            AttributeError: raised if no concreate networking is provided
        """  # noqa: E501
        if not test_services:
            logger.error("Config content can not be Null")
            raise ValueError

        if not test_services.services:
            logger.error("No service was found in the provided config")
            raise ValueError

        _processed_containers: Dict[str, int] = self._compute_container_ranks(
            ranked_services=dict(),
            config_services=test_services,
        )

        _processed_containers_reversed: Dict[int, str] = {
            rank: service for service, rank in _processed_containers.items()
        }
        self.ranked_config_services = RankedContainerServices(
            ranked_services=_processed_containers_reversed
        )  # noqa: E501

    def _compute_container_ranks(
        self,
        *,
        ranked_services: Dict[str, int],
        config_services: ContainerServices,
    ) -> Dict[str, int]:
        """The main method that computes the ranking of the services specified
        in the config.

        Args:
            ranked_services (Dict[str, int]): dict container service name and their assigned ranks
            config_services (ConfigServices): config services generated from the supplied configuration file

        Raises:
            AttributeError: raised to prevent empty configuration properties to be passed to this function
            ValueError: rasied when cyclic dependency is detected

        Returns:
            Dict[str, int]: A list of ranked service models.
        """  # noqa: E501
        _ranked_services: Dict[str, int] = deepcopy(ranked_services)
        if not config_services:
            raise AttributeError("A valid config for test services must be provided")

        rank: int = len(ranked_services.keys())
        if len(config_services.services.keys()) == len(ranked_services.keys()):
            return ranked_services
        else:
            services: Dict[str, ContainerService] = {
                x: y for x, y in config_services.services.items() if x not in _ranked_services  # noqa: E501
            }
            for service_name, service in services.items():
                if not service.depends_on:
                    _ranked_services.update({service_name: rank})
                    rank += 1
                else:
                    if set(service.depends_on).issubset(
                        _ranked_services.keys()
                    ) and not self._check_cyclic_dependency(  # noqa: E501
                        [config_services.services[x] for x in _ranked_services], service_name  # noqa: E501
                    ):
                        _ranked_services.update({service_name: rank})
                        rank += 1
                    elif not set(service.depends_on).issubset(list(config_services.services.keys())):  # noqa: E501
                        raise AttributeError(
                            f"Invalid service name or dependencies detected: {service_name} <=> {set(service.depends_on)}"  # noqa: E501
                        )
            return self._compute_container_ranks(
                ranked_services=_ranked_services, config_services=config_services
            )  # noqa: E501

    @staticmethod
    def _check_cyclic_dependency(
        processed_services: List[ContainerService], dependent_service_name: str
    ) -> bool:  # noqa: E501
        for service in processed_services:
            if set([dependent_service_name]).issubset(service.depends_on):
                return True
        return False
