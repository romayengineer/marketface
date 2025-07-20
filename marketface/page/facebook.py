import sys
sys.path.insert(0, "/home/marketface")

from dataclasses import dataclass
from typing import Optional, Dict, Iterator
from urllib.parse import urlencode


from marketface.data.items import Item
from marketface.logger import getLogger

from playwright.sync_api import TimeoutError, BrowserContext, Page, Locator


logger = getLogger("marketface.pages.facebook")

xbody = "xpath=/html/body"
ximg = "xpath=//img"

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]"
# TODO implement a way to handle all possible xpaths
# for example copy the html of the xbase and parse later in another jov / function
xtitles = [
    f"xpath={xbase}/div[1]/div[1]/h1",
    f"xpath={xbase}/div[1]/h1",
]
xprices = [
    f"xpath={xbase}/div[1]/div[1]/div[1]",
    f"xpath={xbase}/div[1]/div[2]",
]
xdescs = [
    f"xpath={xbase}/div[1]/div[5]/div/div[2]/div[1]",
    f"xpath={xbase}/div[5]",
    f"xpath={xbase}/div[5]/div[2]/div/div[1]",
]
# To check if the session / account is blocked
xblocked = "xpath=/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div"


@dataclass
class LoginCredentials:
    username: str
    password: str


class PageInvalid(Exception):
    pass


class PageBlocked(PageInvalid):
    pass


def drop_leading_nondigits(priceStr: str) -> str:
    while priceStr and not priceStr[0].isdigit():
        priceStr = priceStr[1:]
    return priceStr


def get_number_saparated(priceStr: str) -> Optional[int]:
    """
    if number is for example 123.456123.456
    is (123.456 + 123.456) there are two numbers
    we get the first by getting only 3 numbers after
    separetor either dot or comma
    """
    separators = (".", ",",)
    if not priceStr or not priceStr[0].isdigit():
        return
    sep = None
    number = ""
    use_sep = False
    counter = 0
    for c in priceStr:
        if c in separators:
            sep = c
            use_sep = True
            counter = 0
        if counter != 0 and counter % 4 == 0:
            return int(number)
        if c.isdigit():
            number += c
        elif c in separators:
            pass
        else:
            return int(number)
        if use_sep:
            counter += 1
    return int(number)


def price_str_to_int(priceStr: str) -> Optional[int]:
    if "free" in priceStr.lower():
        logger.info("price string has 'free' returning 0")
        return 0
    newPriceStr = drop_leading_nondigits(priceStr)
    price = get_number_saparated(newPriceStr)
    return price


class WebPage:

    def __init__(
            self,
            context: BrowserContext,
            timeout_ms: Optional[int] = None
        ):
        self.context: BrowserContext = context
        self.timeout_ms = timeout_ms or 5000
        self.pages: Dict[str, Page] = {}
        self.current_page: Optional[Page] = None
        self.logger = getLogger("marketface.pages.facebook.WebPage")
        self.valid_page = True

    def set_current_page(self, page_name:str, page: Page) -> None:
        self.current_page = page
        if page_name in self.pages and self.pages[page_name]:
            self.logger.warning("page already exists in self.pages: '%s'", page_name)
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
        try:
            page.goto(url)
        except TimeoutError as err:
            self.logger.error("Navigation to '%s' failed: '%s'", url, err)
            raise
        return page

    def get_links(
            self,
            xpath: str = "//a",
            page: Optional[Page] = None,
        ) -> Iterator[Locator]:
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        locator = page.locator(xpath)
        count = locator.count()
        for i in range(count):
            yield locator.nth(i)
        if count <= 0:
            self.raise_if_blocked(page)

    def is_blocked(self, page: Page) -> bool:
        blocked_content = page.locator(xblocked).first.text_content()
        return bool(
            blocked_content and "You’re Temporarily Blocked" in blocked_content
        )

    def raise_if_blocked(self, page: Page) -> None:
        if self.is_blocked(page):
            raise PageBlocked("the session / account is blocked")


class MarketplacePage(WebPage):

    def __init__(
            self,
            context: BrowserContext,
            timeout_ms: Optional[int] = None
        ):
        super().__init__(context=context, timeout_ms=timeout_ms)
        self.logger = getLogger("marketface.pages.facebook.MarketplacePage")

    def get_title(self, page: Page) -> Optional[str]:
        self.logger.info("getting title")
        for i, xpath in enumerate(xtitles):
            try:
                return page.locator(xpath).text_content()
            except TimeoutError:
                self.logger.info("selector for title failed nth %s", i)
        self.logger.error("selector for title failed all")

    def get_price(self, page: Page) -> Optional[str]:
        self.logger.info("getting price")
        for i, xpath in enumerate(xprices):
            try:
                return page.locator(xpath).text_content()
            except TimeoutError:
                self.logger.info("selector for price failed nth %s", i)
        self.logger.error("selector for price failed all")

    def get_description(self, page: Page) -> Optional[str]:
        self.logger.info("getting description")
        for i, xpath in enumerate(xdescs):
            try:
                description = page.locator(xpath).text_content()
                if not description:
                    continue
                if "Seller's description" in description:
                    self.logger.warning("description contains 'Seller's description'")
                    continue
                return description
            except TimeoutError:
                self.logger.info("selector for description failed nth %s", i)
        self.logger.error("selector for description failed all")


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
        self.logger = getLogger("marketface.pages.facebook.FacebookPage")
        self.market = MarketplacePage(context=context)

    def login(
            self,
            timeout_ms: Optional[int] = None,
        ) -> "FacebookPage":
        page = self.open(url=self.host, page_name="login", timeout_ms=timeout_ms)
        self.logger.info("login")
        try:
            page.fill("input#email", self.credentials.username)
            page.fill("input#pass", self.credentials.password)
            page.click("button[type='submit']")
        except TimeoutError:
            self.logger.warning("login timeout occurred (possible causes: already logged in, network issues, or page not loading as expected)")
        except Exception as err:
            self.logger.error(err)
        return self

    def market_search_validate(self, page: Page) -> bool:
        return not self.is_blocked(page)

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
        if min_price and min_price > 0:
            params["minPrice"] = str(min_price)
        encoded_params = urlencode(params)
        page.goto(
            f"{self.host}/marketplace/{self.location}/search?{encoded_params}"
        )
        # validate if blocked or any other unusual pages
        self.valid_page = self.market_search_validate(page)
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
        links_found = False
        for link in self.get_market_links():
            href = link.get_attribute("href") or ""
            if href.startswith("/marketplace/item/"):
                market_id = self.get_market_id(url=href)
                links_found = True
                yield f"{self.host}/marketplace/item/{market_id}"
            else:
                raise NotImplementedError("get_market_id only supports relative urls starting with /marketplace/item/")
        if not links_found and self.current_page:
            self.raise_if_blocked(self.current_page)

    def market_item(
            self,
            item_id_or_url: str,
            page: Optional[Page] = None,
        ) -> "FacebookPage":
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        if not item_id_or_url:
            raise ValueError("item_id_or_url is required")
        elif item_id_or_url.isdigit():
            item_url = f"{self.host}/marketplace/item/{item_id_or_url}"
        elif item_id_or_url.startswith("https") and "/marketplace/item/" in item_id_or_url:
            item_url = item_id_or_url
        self.logger.info("goto: %s", item_url)
        page.goto(item_url)
        return self

    def market_details(self, page: Optional[Page] = None, item: Optional[Item] = None) -> Optional[Item]:
        page = page or self.current_page
        if not page:
            raise ValueError("page is required")
        item = item or Item.model_validate({})
        body = str(page.locator(xbody).text_content())
        invalid_strs = [
            "Esta publicación ya no",
            "This listing is far",
            "This Listing Isn't",
        ]
        for invalid_str in invalid_strs:
            if invalid_str in body:
                self.logger.warning("product is far or not available")
                return None
        title = self.market.get_title(page)
        priceStr = self.market.get_price(page)
        description = self.market.get_description(page)
        if not title or not priceStr:
            self.logger.error("title and price are required: title '%s' price '%s'", title, priceStr)
            return None
        price = price_str_to_int(priceStr)
        if price is None:
            self.logger.error("invalid price '%s'", priceStr)
            return None
        item.title = title
        item.priceStr = priceStr
        item.description = description or ""
        if price < 10000:
            item.priceUsd = price
            item.priceArs = round(price * item.usdArsRate, 2)
            item.usd = True
        else:
            item.priceUsd = round(price / item.usdArsRate, 2)
            item.priceArs = price
            item.usd = False
        return item


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
            logger.info(href)
            item = facebook.market_item(
                href
            ).market_details()
            if not item:
                logger.error("could not get item details")
                continue
            item.log()


if __name__ == "__main__":
    test()