from typing import Any, Dict, Optional
from pydantic import BaseModel

class ClientFromEnv(BaseModel):
    version: str="auto"
    timeout: Optional[int]=None
    max_pool_size: Optional[int]=None
    use_ssh_client: bool=False
    ssl_version: Optional[int]=None
    assert_hostname: Optional[bool]=None
    environment: Optional[Dict[str, Any]]=None
    # credstore_env: Optional[Dict[str, Any]]=None


class ClientFromUrl(BaseModel):
    docker_host: Optional[str]=None
    version: str="auto"
    timeout: Optional[int]=None
    tls: Optional[bool]=None
    user_agent: Optional[str]=None
    credstor_env: Optional[Dict[str, Any]]=None
    use_ssh_client: Optional[bool]=None
    max_pool_size: Optional[int]=None


class Login(BaseModel):
    username: Optional[str]=None
    password: Optional[str]=None
    email: Optional[str]=None
    registry: Optional[str]=None
    reauth: Optional[bool]=False
    dockercfg_path: Optional[str]=None