from typing import Optional
from pydantic import BaseModel


class Login(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    registry: Optional[str] = None
    reauth: Optional[bool] = False
    dockercfg_path: Optional[str] = None
