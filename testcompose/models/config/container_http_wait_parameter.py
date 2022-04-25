from pydantic import BaseModel, validator


class HttpWaitParameter(BaseModel):
    http_port: int
    response_status_code: int = 200
    startup_delay_time_ms: int = 20000
    end_point: str = '/'
    use_https: bool = False

    @validator('http_port')
    def validate_http_port(cls, v):
        if not v or not isinstance(v, int):
            raise AttributeError("A valide Integer exposed Http port must be provided")
        return v

    @validator('end_point')
    def validate_end_point(cls, v):
        if not v or not isinstance(v, str):
            raise AttributeError("A valide Http endpoint must be provided")
        return v

    @validator('response_status_code')
    def validate_response_status_code(cls, v):
        if not v or not isinstance(v, int):
            raise AttributeError("A valide Integer Http response code must be provided")
        return v

    @validator('startup_delay_time_ms')
    def validate_startup_delay_time_ms(cls, v):
        if not v or not isinstance(v, int):
            return 20000
        return v
