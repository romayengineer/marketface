"""
Interactive shell for scraping facebook's marketplace

This module provides a set of functions to open the browser
and interact with it in an interactive shell.

The functions are:

* `login`: login to facebook
* `search`: search for something in the marketplace
* `collect_articles`: collects the articles from the current page
* `collect_articles_all`: collects all articles from the current page
* `shorten_item_url`: shorten the url of an item
* `pull_articles`: pull the data from each of the articles
"""

import os.path
import time
from contextlib import contextmanager
from importlib import reload

import requests  # mypy: ignore
from playwright.sync_api import BrowserContext, Page, Locator
from pocketbase.utils import ClientResponseError
from typing import Optional, Dict, Any, Iterator

from marketface import database
from marketface.utils import get_file_name_from_url

# TODO
# from utils import shorten_item_url

reload(database)

# timeout in milliseconds
timeout_ms = 5000

shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page, email, password)",
    "c": "collect_articles(page)",
    "v": "collect_articles_all(page)",
    "p": "play_dynamic.pull_articles(page, context)",
    "h": "play_dynamic.help()",
    "u": "play_dynamic.clear_wrong()",
    "exit": "sys.exit(0)",
}

xbody = "xpath=/html/body"
ximg = "xpath=//img"

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/div[1]"
xtitle = f"xpath={xbase}/div[1]/h1"
xprice = f"xpath={xbase}/div[1]/div[1]"
xdesc = f"xpath={xbase}/div[5]/div/div[2]/div[1]"

sepLine = "-" * 30


def clear_wrong() -> None:
    page = 1
    # query = "priceUsd < 50"
    query = "deleted = true"
    items = []
    while True:
        new_items = database.get_items_list(page, 100, query).items
        if not new_items:
            break
        items.extend(new_items)
        page += 1
    counter = 0
    for item in items:
        # if item.title == "":
        #     continue
        print(item.url, item.price_usd, item.title)
        counter += 1
        # continue # skip update
        database.update_item_by_url(
            item.url,
            {
                "deleted": False,
                "description": "",
                "priceArs": 0,
                "priceUsd": 0,
                "title": "",
            },
        )
    print("counter ", counter)


def help() -> None:
    """
    Prints the getting started tutorial for the
    interactive shell
    """
    print("Getting started tutorial:")
    print("")
    print("1. run `l` this will load facebook's login page")
    print("   login as usual with your user and password")
    print("2. run `s` to open the marketplace and search")
    print("   by default it searches for a macbook")
    print("3. run `c` to collect the marketplace items")
    print("   from the marketplace search page")
    print("")
    for shortcut, command in shortcuts.items():
        print(shortcut, " --> ", command)


def div_by_aria_label(page: Page, label: str) -> Locator:
    return page.locator(f"css=div[aria-label='{label}']")


def collect_articles_links(page: Page, xpath: str = "//a") -> Iterator[Locator]:
    # TODO check why am I getting less items that there actually are
    # I am getting a few less like 4 less items it's related to the
    # selector probably
    # print("collect articles links")
    collections = page.locator(xpath).all()
    for coll in collections:
        href = coll.get_attribute("href") or ""
        if not href.startswith("/marketplace/item/"):
            continue
        yield coll


def create_item(href_full: str, file_name: str = "") -> None:
    try:
        database.get_item_by_url(href_full)
    except ClientResponseError:
        print("record doesn't exist... creating it")
        print("href_full: ", href_full)
        database.create_item(href_full, file_name)


def download_image(href_short: str, img_src: str) -> str:
    """
    Downloads an image from img_src and saves it to a file
    with the name of the href_short but with "/" replaced
    with "_" and ".jpg" at the end

    If the file already exists it doesn't download it again
    """
    base_file_name = get_file_name_from_url(href_short)
    file_name = f"data/images/{base_file_name}.jpg"
    if not os.path.isfile(file_name):
        image_bin = requests.get(img_src).content
        with open(file_name, "wb") as file:
            file.write(image_bin)
    return file_name


@contextmanager
def if_error_print_and_continue():
    try:
        yield
    except Exception as err:
        # if there is any error is ether a timeout
        # or a redirect and the selector is not found
        # continue normally
        print(type(err), err)


class ItemDetails:

    def __init__(self):
        self.title = ""
        self.description = ""
        self.priceStr = ""
        self.price = ""  # price without currency
        self.priceArs = 0.0  # price in Argentinian Pesos
        self.priceUsd = 0.0  # price in Dollars
        self.usdArsRate = 1230.00
        self.isUsd = False
        self.deleted = False

    def print(self) -> None:
        for k, v in self.to_dict().items():
            print(f"{k.ljust(20)}: {v}\n")
        print(sepLine)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deleted": self.deleted,
            "title": self.title,
            "description": self.description,
            "priceStr": self.priceStr,
            "priceArs": self.priceArs,
            "priceUsd": self.priceUsd,
            "usd": self.isUsd,
            "usdArsRate": self.usdArsRate,
        }


def get_item_page_source(url: str, page: Page) -> None:
    file_name = get_file_name_from_url(url)
    locator = "xpath=/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]"
    with open(f"data/source/{file_name}.html", "w") as file:
        inside = page.locator(locator).inner_html()
        file.write(inside)


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
        elif c.isdigit():
            number += c
        if use_sep:
            counter += 1
    return int(number)


def price_str_to_int(priceStr: str) -> Optional[int]:
    newPriceStr = drop_leading_nondigits(priceStr)
    price = get_number_saparated(newPriceStr)
    return price


def get_item_page_details(url: str, page: Page) -> bool:
    item = ItemDetails()
    priceStr = "" # for use before assigment
    with if_error_print_and_continue():
        body = str(page.locator(xbody).text_content())
        invalid_strs = [
            "Esta publicación ya no",
            "This listing is far",
            "This Listing Isn't",
        ]
        for invalid_str in invalid_strs:
            if invalid_str in body:
                print("product is far or not available")
                database.update_item_deleted(url)
                return False
        title = page.locator(xtitle).text_content()
        priceStr = page.locator(xprice).text_content()
        description = page.locator(xdesc).text_content()
        if not title or not priceStr:
            print(f"title and price are required: title '{title}' price '{priceStr}'")
            database.update_item_deleted(url)
            return False
    price = price_str_to_int(priceStr)
    if not price:
        print(f"invalid price {priceStr}")
        database.update_item_deleted(url)
        return False
    item.title = title
    item.priceStr = priceStr
    item.description = description or ""
    if price < 10000:
        item.priceUsd = price
        item.priceArs = round(price * item.usdArsRate, 2)
        item.isUsd = True
    else:
        item.priceUsd = round(price / item.usdArsRate, 2)
        item.priceArs = price
        item.isUsd = False
    item.print()
    return database.update_item_by_url(url, item.to_dict())


def page_of_items(pages: int = 1000, interactive: bool = False) -> Iterator:
    page = 1
    while True:
        items = database.get_items_incomplete(page, pages).items
        if not items:
            break
        for item in items:
            # filter deleted elements
            if item.deleted:
                continue
            yield item
        if interactive:
            inp = input("Continue? (Y/n): ")
            if inp not in ["y", ""]:
                break
        page += 1


def open_new_page(context: BrowserContext, timeout: Optional[int] = timeout_ms) -> Page:
    timeout = timeout or timeout_ms
    page: Page = context.new_page()
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    print("New Page")
    return page


def open_article_page(context: BrowserContext, url: str) -> bool:
    new_page = open_new_page(context)
    print("Article URL:      ", url)
    try:
        new_page.goto(url)
        time.sleep(2)
        get_item_page_details(url, new_page)
        # TODO get_item_page_source(item.url, new_page)
    except Exception as err:
        print("Error: ", err)
        database.update_item_deleted(url)
        new_page.close()
        return False
    new_page.close()
    return True


def pull_articles(page: Page, context: BrowserContext) -> None:
    """
    similar to collect_articles but this function
    open each of the urls stored in the database and
    pulls the title, description, prince and other
    details of the marketplace items

    shortcut: p
    """
    # TODO remove pages=1 is just for testing and get only one
    for item in page_of_items():
        open_article_page(context, item.url)
        time.sleep(2)


def login(page: Page, email: str, password: str) -> bool:
    # TODO log error
    try:
        page.goto("https://www.facebook.com")
        page.fill("input#email", email)
        page.fill("input#pass", password)
        page.click("button[type='submit']")
        return True
    except Exception:
        return False


def search(page: Page, url: Optional[str] = None) -> None:
    if not url:
        url = "https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook%2032&exact=false"
    page.goto(
        url,
    )
