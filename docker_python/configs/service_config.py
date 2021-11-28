from typing import Dict, List, Set, Tuple
from docker_python.models.config import ITestConfig, ITestConfigServices, RankedServices, RankedServiceKey
from docker_python.log_setup import stream_logger

logger = stream_logger(__name__)


class Config:
    def __init__(self, test_services: ITestConfig) -> None:
        self._get_container_spawn_precedence(test_services)

    @property
    def ranked_itest_config_services(self) -> RankedServices:
        return self._ranked_it_services

    @ranked_itest_config_services.setter
    def ranked_itest_config_services(self, ranked_services: RankedServices) -> None:
        self._ranked_it_services = ranked_services

    def _get_container_spawn_precedence(self, test_services: ITestConfig) -> None:
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

        if all([test_services.network.auto_create, test_services.network.auto_create]):
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
        if not unprocessed_containers and not processed_containers:
            raise ValueError("Processed and Unprocessed container are both empty")

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
