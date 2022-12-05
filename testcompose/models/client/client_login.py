from typing import Any, Dict, Optional
from pydantic import BaseModel, validator
from docker.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_POOL_SIZE


class ClientFromEnv(BaseModel):
    use_ssh_client: bool = False
    ssl_version: Optional[int] = None
    assert_hostname: Optional[bool] = None
    environment: Optional[Dict[str, Any]] = None
    version: str = "auto"
    timeout: Optional[int] = DEFAULT_TIMEOUT_SECONDS
    max_pool_size: Optional[int] = DEFAULT_MAX_POOL_SIZE

    @validator('version')
    def validate_version(cls, v):
        return v or "auto"

    @validator('timeout')
    def validate_timeout(cls, v):
        return v or DEFAULT_TIMEOUT_SECONDS

    @validator('max_pool_size')
    def validate_max_pool_size(cls, v):
        return v or DEFAULT_MAX_POOL_SIZE


class ClientFromUrl(BaseModel):
    docker_host: Optional[str] = None
    tls: Optional[bool] = None
    user_agent: Optional[str] = None
    credstor_env: Optional[Dict[str, Any]] = None
    use_ssh_client: Optional[bool] = None
    timeout: Optional[int] = DEFAULT_TIMEOUT_SECONDS
    max_pool_size: Optional[int] = DEFAULT_MAX_POOL_SIZE
    version: str = "auto"

    @validator('version')
    def validate_version(cls, v):
        return v or "auto"

    @validator('timeout')
    def validate_timeout(cls, v):
        return v or DEFAULT_TIMEOUT_SECONDS

    @validator('max_pool_size')
    def validate_max_pool_size(cls, v):
        return v or DEFAULT_MAX_POOL_SIZE
