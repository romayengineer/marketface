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

import database
import requests  # mypy: ignore
from playwright.sync_api import TimeoutError
from pocketbase.utils import ClientResponseError

from marketface.utils import get_file_name_from_url

# TODO
# from utils import shorten_item_url

reload(database)

shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page, email, passwd)",
    "c": "collect_articles(page)",
    "v": "collect_articles_all(page)",
    "p": "play_dynamic.pull_articles(page, context)",
    "h": "play_dynamic.help()",
    "u": "play_dynamic.clear_wrong()",
    "exit": "sys.exit(0)",
}

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/"
xbody = "xpath=/html/body"
xtitle = f"xpath={xbase}div[1]/h1"
xprice = f"xpath={xbase}div[1]/div[1]"
xdesc = f"xpath={xbase}div[5]/div/div[2]/div[1]"
ximg = "xpath=//img"

lowercase = [chr(n) for n in range(ord("a"), ord("a") + 26)] + ["ñ"]  # Spanish letter
uppercase = [chr(n) for n in range(ord("A"), ord("A") + 26)] + ["Ñ"]
letters = lowercase + uppercase
numbers = [str(n) for n in range(10)]
especial = [
    " ",
    "’",
    "'",
    '"',
    ".",
    ",",
    ";",
    "!",
    "?",
    "_",
    "-",
    "/",
    "\\",
    "|",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
]
alphabet = letters + numbers + especial

sepLine = "-" * 30


def clear_wrong():
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


def help():
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


def div_by_aria_label(page, label):
    return page.locator(f"css=div[aria-label='{label}']")


def collect_articles_links(page, xpath="//a"):
    # TODO check why am I getting less items that there actually are
    # I am getting a few less like 4 less items it's related to the
    # selector probably
    # print("collect articles links")
    collections = page.locator(xpath).all()
    for coll in collections:
        href = coll.get_attribute("href")
        if not href.startswith("/marketplace/item/"):
            continue
        yield coll


def create_item(href_full, file_name=""):
    try:
        database.get_item_by_url(href_full)
    except ClientResponseError:
        print("record doesn't exist... creating it")
        print("href_full: ", href_full)
        database.create_item(href_full, file_name)


def download_image(href_short, img_src):
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


def oneline(text):
    """
    puts everything in one line and removes unwanted characters
    like for example emojis
    """
    text = text.replace("\n", " ")
    newText = ""
    i = 0
    while i < len(text):
        c = text[i]
        if c == " ":
            newText += " "
            i += 1
            while i < len(text):
                c = text[i]
                if c == " ":
                    i += 1
                else:
                    break
            continue
        if c not in alphabet:
            i += 1
            continue
        newText += c
        i += 1
    return newText.strip()


def firstnumbers(numberStr):
    i = 0
    newNumber = ""
    while i < len(numberStr):
        c = numberStr[i]
        if c not in numbers:
            break
        newNumber += c
        i += 1
    return newNumber


class ItemDetails:

    def __init__(self):
        self.title = ""
        self.description = ""
        self.priceStr = ""
        self.price = ""  # price without currency
        self.priceArs = 0  # price in Argentinian Pesos
        self.priceUsd = 0  # price in Dollars
        self.isUsd = False
        self.usdArsRate = 1205.00


def get_item_page_source(url: str, page) -> None:
    file_name = get_file_name_from_url(url)
    locator = "xpath=/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]"
    with open(f"data/source/{file_name}.html", "w") as file:
        inside = page.locator(locator).inner_html()
        file.write(inside)


def get_item_page_details(url, page):
    # TODO save into pocketbase
    title = ""
    description = ""
    priceStr = ""
    price = ""  # price without currency
    priceArs = 0  # price in Argentinian Pesos
    priceUsd = 0  # price in Dollars
    isUsd = False
    # TODO update this rate put it somewhere else
    # exchange rate of 2024-08-31
    usdArsRate = 1205.00
    with if_error_print_and_continue():
        if "Esta publicación ya no" in page.locator(xbody).text_content():
            database.update_item_deleted(url)
            return
        if "This listing is far" in page.locator(xbody).text_content():
            database.update_item_deleted(url)
            return
        if "This Listing Isn't" in page.locator(xbody).text_content():
            database.update_item_deleted(url)
            return
        title = oneline(page.locator(xtitle).text_content())
        priceStr = oneline(page.locator(xprice).text_content())
        description = oneline(page.locator(xdesc).text_content())
    # if you are in a different location change this rate conversion logic
    if priceStr and priceStr.startswith("ARS"):
        # remove first 3 characters from ARS
        # so far nobody use cents but if they do this will fail
        # conver to float in that case
        price = priceStr.partition(" ")[0][3:]
    elif priceStr and priceStr[0] in numbers:
        price = priceStr.partition(" ")[0]
    else:
        database.update_item_deleted(url)
        print("Currency must be in ARS!")
        return
    price = price.replace(",", "").replace(".", "")
    # sometimes the price is followed by a scratched old price
    # the text_content puts this text on the same word meaning
    # it is not separated by an space in that case only
    # get the first numbers and ignore everything after that
    # e.g the price may look like this ARS200000ARS230000
    # in this case we want the first price 200000
    price = int(firstnumbers(price))
    if price < 10000:
        priceUsd = price
        priceArs = round(price * usdArsRate, 2)
        isUsd = True
    else:
        priceUsd = round(price / usdArsRate, 2)
        priceArs = price
        isUsd = False
    print("title:        ", title)
    print("price:        ", priceStr)
    print("priceUsd:     ", priceUsd)
    print("priceArs:     ", priceArs)
    print("isUsd:        ", isUsd)
    print("description:  ", description)
    print(sepLine)
    body_params = {
        "deleted": False,
        "description": description,
        "priceArs": priceArs,
        "priceUsd": priceUsd,
        "title": title,
        "usd": isUsd,
        "usdArsRate": usdArsRate,
    }
    database.update_item_by_url(url, body_params)


def page_of_items(pages=1000):
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
        inp = input("Continue? (Y/n): ")
        if inp not in ["y", ""]:
            break
        page += 1


def pull_articles(page, context):
    """
    similar to collect_articles but this function
    open each of the urls stored in the database and
    pulls the title, description, prince and other
    details of the marketplace items

    shortcut: p
    """
    # TODO remove pages=1 is just for testing and get only one
    for item in page_of_items():
        new_page = context.new_page()
        new_url = item.url
        print("new_url: ", new_url)
        try:
            new_page.goto(new_url)
        except TimeoutError as err:
            print("TimeoutError: ", err)
        time.sleep(2)
        # TODO
        get_item_page_details(item.url, new_page)
        # get_item_page_source(item.url, new_page)
        new_page.close()
        time.sleep(2)


def login(page, email: str, passwd: str) -> bool:
    # TODO log error
    try:
        page.goto("https://www.facebook.com")
        page.fill("input#email", email)
        page.fill("input#pass", passwd)
        page.click("button[type='submit']")
        return True
    except Exception:
        return False


def search(page):
    page.goto(
        "https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false"
    )


def test(page):
    login(page)
    login(page)
