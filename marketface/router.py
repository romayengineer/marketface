import re
from playwright.sync_api import BrowserContext, Route


# --- PERFORMANCE BOOST - THIS IS THE NEW CODE ---
class Router:


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


    def apply_rules(self) -> None:
        # Apply this routing rule to the entire browser context.
        # The "**" is a glob pattern that matches all URLs.
        self.context.route("**/*", self.handle_route)
        print("🚀 Performance mode enabled: Blocking images, fonts, and stylesheets.")


    def handle_route(self, route: Route) -> None:
        # Check if the request's resource type is in our blocked list
        if route.request.resource_type in self.blocked_resource_types:
            # print(f"🚫 Blocking [resource]: {route.request.url}")
            return route.abort()

        # Check if the request's URL matches any of our blocked domains
        for domain in self.blocked_domains:
            if re.search(domain, route.request.url):
                # print(f"🚫 Blocking [domain]: {route.request.url}")
                return route.abort()

        # If the request is not blocked, let it continue
        return route.continue_()