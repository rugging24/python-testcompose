from docker_python.configs.service_config import Config
from docker_python.models.config import (
      Services, 
      RankedServices, 
      RankedServiceKey
)
from config_fixtures import more_containers


def test_get_config_services_more_containers(more_containers):
      config_content = Config(config_content=more_containers)
      computed_services: RankedServices = config_content.get_config_services()

      expected_services: Services = Services(**more_containers)
      expected_itest_mappers = expected_services.services
      expected_ranked_services = RankedServices(**{
            RankedServiceKey.SERVICES: {
                  i.spawn_rank: i
                  for i in expected_itest_mappers
            }
      })

      assert computed_services
      assert len(computed_services.services) == len(expected_ranked_services.services)
      assert list(computed_services.services.keys()) == list(expected_ranked_services.services.keys())

      for rank, service in expected_ranked_services.services.items():
            assert service == computed_services.services[rank]