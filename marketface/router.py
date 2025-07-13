import re
import time
import threading
from abc import ABC, abstractmethod

from typing import Optional
from urllib.parse import urlparse, ParseResult

from marketface.logger import getLogger

from playwright.sync_api import BrowserContext, Route


logger = getLogger("marketface.router")


class Router(ABC):

    @abstractmethod
    def __init__(self, context: BrowserContext) -> None:
        ...

    @abstractmethod
    def apply_rules(self) -> None:
        ...

    @abstractmethod
    def handle_all_routes(self, route: Route) -> None:
        ...


class RateLimiter(ABC):

    @abstractmethod
    def acquire(self) -> None:
        ...


class TokenBucketRateLimiter(RateLimiter):

    def __init__(self, capacity: float, rate_limit: float) -> None:
        self.capacity = capacity # constant
        self.rate_limit = rate_limit # constant
        if self.rate_limit <= 0 or self.capacity <= 0:
            raise ValueError("Rate limit and capacity have to be > 0")
        if self.rate_limit > self.capacity:
            raise ValueError("Rate limit exceeds bucket capacity")
        self.tokens = capacity
        self.last_refill_time = time.perf_counter()
        self.lock = threading.Lock()
        # it would be more semantically sound to set acquire_return_time to None
        # but that requires to do an if not None check and that
        # slows down the acquire function, so better to set this here
        # and skip the check
        self.acquire_return_time: float = time.perf_counter()


    def refill_tokens(self) -> None:
        refill_time = time.perf_counter()
        time_passed = refill_time - self.last_refill_time
        new_tokens = time_passed * self.rate_limit
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill_time = refill_time


    def acquire(self, tokens_needed: int) -> None:
        if tokens_needed > self.capacity:
            raise ValueError("Tokens needed exceeds bucket capacity")

        while True:
            with self.lock:
                self.refill_tokens()
                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    # Exit the loop and let the worker proceed
                    sleeped_for = time.perf_counter() - self.acquire_return_time
                    if sleeped_for > 0.5:
                        logger.info("time elapsed since acquire returned %s", sleeped_for)
                    self.acquire_return_time = time.perf_counter()
                    return

            # If we're here, we didn't have enough tokens.
            # Sleep outside the lock to allow other threads to run.
            # Sleep time can be small; it's just to prevent busy-waiting.
            time.sleep(0.01)


# --- PERFORMANCE BOOST - THIS IS THE NEW CODE ---
class FacebookRouter(Router):


    def __init__(self, context: BrowserContext) -> None:
        self.context = context
        # Define a set of resource types to allow
        self.allowed_resource_types = {"document", "script", "fetch", "xhr", "other"}
        # Define a list of domains to allow
        self.allowed_domains = ["fbcdn.net", "facebook.com", "fbsbx.com"]
        # counters
        self.counter_requested_all = 0
        self.counter_requested_allowed = 0
        self.limiter = TokenBucketRateLimiter(capacity=30, rate_limit=30)


    def apply_rules(self) -> None:
        # Apply this routing rule to the entire browser context.
        # The "**" is a glob pattern that matches all URLs.
        self.context.route("**/*", self.handle_all_routes)
        print("🚀 Performance mode enabled: Blocking images, fonts, and stylesheets.")


    def get_path_extension(self, url_parsed: ParseResult) -> Optional[str]:
        match = re.search(r"\.[a-z0-9]{1,5}$", url_parsed.path)
        if match:
            return match.group()


    def is_extension_not_required(self, path_extension: str) -> bool:
        return path_extension in {".mp4", ".css", ".ico", ".kf", ".wasm"}


    def is_extension_not_js(self, path_extension: str) -> bool:
        return path_extension != ".js"


    def calculate_blocked_percentage(self) -> float:
        return 100 * (1 - self.counter_requested_allowed / self.counter_requested_all)


    def is_domain_allowed(self, hostname: str) -> bool:
        return any(
            hostname.endswith(domain) for domain in self.allowed_domains
        )


    def handle_all_routes(self, route: Route) -> None:
        # self.counter_requested_all += 1

        url_parsed: ParseResult = urlparse(route.request.url)
        hostname: str = url_parsed.hostname or ""

        # block request if resource types not allowed
        if route.request.resource_type not in self.allowed_resource_types:
            logger.debug("🚫 Blocking [resource]: %s", route.request.url)
            return route.abort()

        # block request if domains not allowed
        if not self.is_domain_allowed(hostname):
            logger.debug("🚫 Blocking [domain]: %s", route.request.url)
            return route.abort()

        # block request if path has extension and does not end in .js
        path_extension = self.get_path_extension(url_parsed)
        if path_extension and self.is_extension_not_js(path_extension):
            logger.debug("🚫 Blocking [path]: %s", url_parsed.path)
            return route.abort()

        # apply rate limiting logic
        self.limiter.acquire(tokens_needed=1)

        # self.counter_requested_allowed += 1

        # uncomment this for debugging
        # after testing these rules block around 50% of requests
        # block_percentage = self.calculate_blocked_percentage()
        # logger.info("request blocked percentage: %.2f%%", block_percentage)


        # If the request is not blocked and request rate is within limits let it continue
        return route.continue_()