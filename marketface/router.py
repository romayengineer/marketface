import re
import time
import threading
from abc import ABC, abstractmethod

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
        # Define the types of resources we want to block to speed up loading.
        # Common resource types: 'image', 'stylesheet', 'font', 'media', 'script'
        # Be careful blocking 'script' as it can break website functionality.
        self.blocked_resource_types = [
            "image",
            # whitout the stylesheets the selectors don't work
            # and we cannot get the data from the site
            # "stylesheet",
            "font",
            "media"
        ]
        # Define a list of domains to block (e.g., tracking, ads)
        # This uses regular expressions for flexible matching.
        self.blocked_domains = [
            r"googletagmanager\.com",
            r"google-analytics\.com",
            r"doubleclick\.net"
        ]
        self.limiter = TokenBucketRateLimiter(capacity=30, rate_limit=30)


    def apply_rules(self) -> None:
        # Apply this routing rule to the entire browser context.
        # The "**" is a glob pattern that matches all URLs.
        self.context.route("**/*", self.handle_all_routes)
        print("🚀 Performance mode enabled: Blocking images, fonts, and stylesheets.")


    def handle_all_routes(self, route: Route) -> None:
        # Check if the request's resource type is in our blocked list
        if route.request.resource_type in self.blocked_resource_types:
            # print(f"🚫 Blocking [resource]: {route.request.url}")
            return route.abort()

        # Check if the request's URL matches any of our blocked domains
        for domain in self.blocked_domains:
            if re.search(domain, route.request.url):
                # print(f"🚫 Blocking [domain]: {route.request.url}")
                return route.abort()
        # apply rate limiting logic
        self.limiter.acquire(tokens_needed=1)
        # If the request is not blocked, let it continue
        return route.continue_()