from contextlib import contextmanager

from pocketbase.utils import ClientResponseError

from marketface.logger import getLogger


logger = getLogger("marketface.data.errors")


@contextmanager
def skip(*error_catchers):
    """
    skip errors like item with url already exists.
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

def all_exceptions(message: str):
    def catcher(err: Exception):
        logger.error("exception in %s: %s", message, err)
    return catcher
