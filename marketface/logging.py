import sys
import logging
from logging import DEBUG, INFO, Logger
from typing import Any


log_level = logging.INFO
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    # useful for running locally to set LOGLEVEL=DEBUG
    # LOGLEVEL=DEBUG python3 pulumirunner/scripts/tenant_consumer.py
    level=log_level,
    format=log_format,
    stream=sys.stdout,
)


def getLogger(*args: Any, **kwargs: Any) -> Logger:
    logger = logging.getLogger(*args, **kwargs)
    return logger