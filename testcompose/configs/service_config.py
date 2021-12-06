from typing import Dict, List, Set, Tuple
from testcompose.models.config import ITestConfig, ITestConfigServices, RankedServices, RankedServiceKey
from testcompose.log_setup import stream_logger

logger = stream_logger(__name__)


class Config:
    """This class consumes the model created from a config file.
    This is an important class that sets the precedence of how the
    different containers are to be started and stopped. Usually, the
    precedence are set correctly if the `depends_on` parameter of the
    config is set. Cyclic dependency will fail the test before it starts.

    Args:
        test_services (ITestConfig): model resulting from a parsed configuration file.
    """

    def __init__(self, test_services: ITestConfig) -> None:
        self._get_container_spawn_precedence(test_services)

    @property
    def ranked_itest_config_services(self) -> RankedServices:
        """Object containing the ordered services from the config

        Returns:
            RankedServices: ranked container services
        """
        return self._ranked_it_services

    @ranked_itest_config_services.setter
    def ranked_itest_config_services(self, ranked_services: RankedServices) -> None:
        self._ranked_it_services = ranked_services

    def _get_container_spawn_precedence(self, test_services: ITestConfig) -> None:
        """

        Args:
            test_services (ITestConfig): model resulting from a parsed configuration file.

        Raises:
            ValueError: raised if test_services is `null`
            AttributeError: raised if no concreate networking is provided
        """
        _config_services: Dict[Tuple[int, str], ITestConfigServices] = dict()
        if not test_services:
            logger.error("Config content can not be Null")
            raise ValueError

        if not test_services.services:
            logger.error("No service was found in the provided config")
            raise ValueError

        _processed_containers: List[ITestConfigServices] = self._compute_container_ranks(
            processed_containers=list(),
            processed_container_names=set(),
            unprocessed_containers=test_services.services,
        )

        for _rank, _service in enumerate(_processed_containers):
            _config_services.update({(_rank, _service.name): _service})

        if all([test_services.network.auto_create, test_services.network.use_random_network]):
            raise AttributeError(
                "Both auto_create and use_random_network options of network can not be True!!"
            )

        self.ranked_itest_config_services = RankedServices(
            **{RankedServiceKey.SERVICES: _config_services, RankedServiceKey.NETWORK: test_services.network}
        )

    def _compute_container_ranks(
        self,
        processed_containers: List[ITestConfigServices],
        processed_container_names: Set[str],
        unprocessed_containers: List[ITestConfigServices],
    ) -> List[ITestConfigServices]:
        """The main method that computes the ranking of the services specified
        in the config.

        Args:
            processed_containers (List[ITestConfigServices]): Container object of the services to be tested
            processed_container_names (Set[str]): the names of the services as specified in the configs that had been ranked
            unprocessed_containers (List[ITestConfigServices]): the names of the services as specified in
                                                                the configs yet to be ranked

        Raises:
            AttributeError: raised to prevent both unprocessed_containers and processed_containers from being `null`
            ValueError: rasied when cyclic dependency is detected

        Returns:
            List[ITestConfigServices]: A list of ranked service models.
        """
        if not unprocessed_containers and not processed_containers:
            raise AttributeError("Processed and Unprocessed container are both empty")

        if not unprocessed_containers:
            return processed_containers
        else:
            passes: Set[str] = set()
            for _container in unprocessed_containers:
                passes.add(_container.name)
                if not _container.depends_on:
                    processed_containers.append(_container)
                    processed_container_names.add(_container.name)
                else:
                    if set(_container.depends_on).issubset(processed_container_names):
                        processed_containers.append(_container)
                        processed_container_names.add(_container.name)
                    elif not set(_container.depends_on).issubset(processed_container_names) and set(
                        _container.depends_on
                    ).issubset(passes):
                        raise ValueError(
                            f"Cyclic container dependencies detected: {processed_container_names} <=> {set(_container.depends_on)}"
                        )
            passes.clear()
            del passes
            return self._compute_container_ranks(
                processed_containers,
                processed_container_names,
                [x for x in unprocessed_containers if x.name not in processed_container_names],
            )
