import logging
from typing import TextIO


def stream_logger(logger_name) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    handler: logging.StreamHandler[TextIO] = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger
