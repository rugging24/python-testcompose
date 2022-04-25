from pydantic import BaseModel, validator


class LogWaitParameter(BaseModel):
    log_line_regex: str
    wait_timeout_ms: int = 60000
    poll_interval_ms: int = 10000

    @validator('log_line_regex')
    def validate_log_line_regex(cls, v):
        if not v:
            raise AttributeError("log_line_prefix must be set")
        return v
