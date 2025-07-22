from typing import Callable
from contextlib import contextmanager

from pocketbase.utils import ClientResponseError
from playwright.sync_api import TimeoutError

from marketface.logger import getLogger



logger = getLogger("marketface.data.errors")


@contextmanager
def skip(*error_catchers):
    """
    skip common errors that are handled always the same way
    """
    try:
        yield
    except Exception as err:
        for error_catcher in error_catchers:
            if error_catcher(err):
                return
        raise err

def url_not_unique(err: ClientResponseError) -> bool:
    if not isinstance(err, ClientResponseError):
        return False
    if err.status == 400:
        code: str = err.data.get('data', {}).get("url", {}).get("code", "")
        if not isinstance(code, str):
            return False
        if code == "validation_not_unique":
            logger.debug("item already exists")
            return True
    return False

def description_max_text(err: ClientResponseError) -> bool:
    if not isinstance(err, ClientResponseError):
        return False
    if err.status == 400:
        code: str = err.data.get("data", {}).get("description", {}).get("code", "")
        if not isinstance(code, str):
            return False
        error_code = "validation_max_text_constraint"
        if code == error_code:
            logger.warning("%s: description", error_code)
            return True
    return False

def playwright_timeout(err: TimeoutError) -> bool:
    if not isinstance(err, TimeoutError):
        return False
    logger.error("playwright timeout")
    return True

def all_exceptions(message: str) -> Callable:
    def catcher(err: Exception) -> bool:
        logger.error("exception in %s: %s %s", message, type(err), err)
        return True
    return catcher
