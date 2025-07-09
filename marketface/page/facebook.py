from dataclasses import dataclass
from typing import Optional, Dict, Iterator
from urllib.parse import urlencode

from playwright.sync_api import TimeoutError, BrowserContext, Page, Locator


@dataclass
class LoginCredentials:
    username: str
    password: str


class WebPage:

    def __init__(
            self,
            context: BrowserContext,
            timeout_ms: Optional[int] = None
        ):
        self.context: BrowserContext = context
        self.timeout_ms = timeout_ms or 5000 # 5 seconds
        self.pages: Dict[str, Page] = {} # TODO
        self.current_page: Optional[Page] = None

    def set_current_page(self, page_name:str, page: Page) -> None:
        self.current_page = page
        if page_name in self.pages and self.pages[page_name]:
            print(f"Warning - page already exists in self.pages: '{page_name}'")
        self.pages[page_name] = page

    def new_page(
            self,
            page_name: str,
            timeout_ms: Optional[int] = None,
        ) -> Page:
        timeout_ms = timeout_ms or self.timeout_ms
        page: Page = self.context.new_page()
        self.set_current_page(page_name, page)
        page.set_default_navigation_timeout(timeout_ms)
        page.set_default_timeout(timeout_ms)
        return page

    def open(
            self,
            url: str,
            page_name: Optional[str] = None,
            timeout_ms: Optional[int] = None,
        ) -> Page:
        page_name = page_name or url
        page = self.new_page(page_name, timeout_ms=timeout_ms)
        page.goto(url)
        return page

    def get_links(
            self,
            xpath: str = "//a",
            page: Optional[Page] = None,
        ) -> Iterator[Locator]:
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        links = page.locator(xpath).all()
        for link in links:
            yield link


class FacebookPage(WebPage):

    def __init__(
            self,
            context: BrowserContext,
            credentials: LoginCredentials,
            location: str = "buenosaires",
            host: str = "https://www.facebook.com",
        ):
        super().__init__(context)
        self.credentials = credentials
        self.host = host
        self.location = location

    def login(
            self,
            timeout_ms: Optional[int] = None,
        ) -> "FacebookPage":
        page = self.open(url=self.host, page_name="login", timeout_ms=timeout_ms)
        try:
            page.fill("input#email", self.credentials.username)
            page.fill("input#pass", self.credentials.password)
            page.click("button[type='submit']")
        except TimeoutError:
            print("Warning - already log in")
        except Exception as err:
            print("Error - ", err)
        return self

    def market_search(
            self,
            query: str,
            min_price: Optional[int] = None,
            exact: bool = False,
            page: Optional[Page] = None,
        ) -> "FacebookPage":
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        if not query:
            raise ValueError("query is required")
        params = {"query": query, "exact": str(exact)}
        if min_price:
            params["minPrice"] = str(min_price)
        encoded_params = urlencode(params)
        page.goto(
            f"{self.host}/marketplace/{self.location}/search?{encoded_params}"
        )
        return self

    def get_market_id(
            self,
            url: str,
        ) -> str:
        """
        Takes the full url of a marketplace item and shortens it
        to the following format
        /marketplace/item/<number>
        """
        start = "/marketplace/item/"
        if not url.startswith(start):
            raise ValueError(f"market item url must start with {start}")
        i = len(start)
        u = len(url)
        if not u > i:
            raise ValueError(f"market item url does not contain id {url}")
        # loop through each character of the url
        e = i
        while e < u:
            # if the character is not a digit break the loop
            if not url[e].isdigit():
                break
            # move to the next character
            e += 1
        market_id = url[i:e]
        return market_id

    def get_market_links(
            self,
            xpath: str = "//a",
            page: Optional[Page] = None,
        ) -> Iterator[Locator]:
        for link in self.get_links(page=page):
            href = link.get_attribute("href") or ""
            if "/marketplace/item/" not in href:
                continue
            yield link

    def get_market_href(
            self,
        ) -> Iterator[str]:
        for link in self.get_market_links():
            href = link.get_attribute("href") or ""
            if href.startswith("/marketplace/item/"):
                market_id = self.get_market_id(url=href)
                yield f"{self.host}/marketplace/item/{market_id}"
            else:
                raise NotImplementedError("TODO")

    def market_item(
            self,
            item_id: str,
            page: Optional[Page] = None,
        ) -> "FacebookPage":
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        page.goto(
            f"{self.host}/marketplace/item/{item_id}"
        )
        return self


def test():

    import sys
    sys.path.insert(0, "/home/marketface")

    from playwright.sync_api import sync_playwright

    from marketface.scrap_marketplace import email, password
    from marketface.scrap_marketplace import get_browser_context

    with sync_playwright() as p:
        context = get_browser_context(p)
        facebook = FacebookPage(
            context=context,
            credentials=LoginCredentials(username=email, password=password),
        )
        facebook.login(
                timeout_ms=10000,
            ).market_search(
                query="iphone 10"
            )

        for href in facebook.get_market_href():
            print(href)


if __name__ == "__main__":
    test()