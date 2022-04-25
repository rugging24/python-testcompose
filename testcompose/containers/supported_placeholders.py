from dataclasses import dataclass


@dataclass(frozen=True)
class SupportedPlaceholders:
    SELF_HOST: str = 'self'
    CONTAINER_HOSTNAME: str = 'container_hostname'
    EXTERNAL_PORT: str = 'external_port'
    CONTAINER_HOST_ADDRESS: str = 'container_host_address'
