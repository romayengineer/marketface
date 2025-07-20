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
from pocketbase.models.utils.base_model import BaseModel
from typing import Optional, Dict, Any, Iterator

from marketface import database
from marketface.utils import get_file_name_from_url
from marketface.logger import getLogger
from marketface.page.facebook import price_str_to_int

# TODO
# from utils import shorten_item_url

logger = getLogger("marketface.play_dynamic")

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


def create_item(href_full: str, file_name: Optional[str] = None) -> Optional[BaseModel]:
    try:
        model = database.create_item(href_full, file_name)
        logger.info("record doesn't exist... created: %s", href_full)
        return model
    except ClientResponseError as err:
        if err.status == 400:
            data: Dict = err.data.get('data', {})
            key_url: Dict = data.get("url", {})
            code = key_url.get("code", "")
            if isinstance(code, str) and code == "validation_not_unique":
                logger.info("item already exists")
                return
        logger.error("unexpected error status code 400 data %s", data)


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

