#!/usr/bin/env python3
import argparse
import os
import sys
import time
from argparse import ArgumentTypeError
from importlib import reload

from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, Route, Locator

sys.path.insert(0, os.getcwd())

# this is for quick development cycle as I reload this module
# dynamically and I update the code to see the changing without
# reloading the script or browser
from marketface import play_dynamic
from marketface.utils import shorten_item_url
from marketface.creds import read_creds
from marketface.logger import getLogger
from marketface.router import FacebookRouter


logger = getLogger("marketface.scrap_marketplace")

links_processed = set()

# Initialize parser
argParser = argparse.ArgumentParser()

# Adding optional argument
argParser.add_argument("-e", "--Email", type=str, help="email to login")
argParser.add_argument("-p", "--Password", type=str, help="password to login")
argParser.add_argument(
    "-s", "--Show",
    action="store_true",
    help="show browser? headless or not?"
)

# Read arguments from command line
args = argParser.parse_args()

print("show: ", args.Show)
headless = not args.Show

creds = read_creds(os.path.join(os.getcwd(), "creds.json"))

email: str = args.Email or creds.get("email", "")
password: str = args.Password or creds.get("password", "")

if not email or not password:
    raise ArgumentTypeError("need to pass login credentials, email and password")


storage_state_file="/home/marketface/browser_context.json"


def interactive_save_browser_context(context: BrowserContext) -> None:
    """
    This is to refresh the session once is log out.
    to break out of the loop just kill the process once the manual login is successful.
    the reason the loggin is manual is because of captcha that has to be resolved manually
    just once in the first login after that the session is stored in the browser_context.json
    """
    while True:
        logger.info("saving browser context")
        context.storage_state(path=storage_state_file)
        time.sleep(10)


def get_browser_context(p: Playwright, with_rules: bool = True) -> BrowserContext:
    browser: Browser = p.chromium.launch(headless=headless, slow_mo=200)
    print("New Browser")
    context: BrowserContext = browser.new_context(storage_state=storage_state_file)
    if with_rules:
        router = FacebookRouter(context)
        router.apply_rules()
    print("New Context")
    return context


def play_repl(context: BrowserContext, page: Page) -> None:
    # eval may use context and/or page so keep these arguments
    # these variables are used dynamically by eval
    play_dynamic.help()
    while True:
        try:
            command = input(">>> ").strip()
            if command == "":
                continue
            if command == "exit":
                sys.exit(0)
            reload(play_dynamic)
            # if command is a shortcut translate to code and execute
            command = play_dynamic.shortcuts.get(command, command)
            eval(command)
        except (KeyboardInterrupt, Exception) as err:
            print(err)


def collect_item_data(link: Locator) -> None:
    href_full = link.get_attribute("href") or ""
    href_short = shorten_item_url(href_full)
    href_full = "https://www.facebook.com" + href_short
    imgs = link.locator(play_dynamic.ximg).all()
    img_src = imgs[0].get_attribute("src") if len(imgs) > 0 else ""
    # file_name = play_dynamic.download_image(href_short, img_src)
    file_name = None
    play_dynamic.create_item(href_full, file_name)


def collect_articles(page: Page) -> None:
    counter = 0
    for link in play_dynamic.collect_articles_links(page):
        href = link.get_attribute("href") or ""
        if href in links_processed:
            counter += 1
            continue
        collect_item_data(link)
        links_processed.add(href)
        counter += 1
    print("first ", counter)


def collect_articles_all(page: Page) -> None:
    # collects all articles including the ones
    # from outside your search
    before = -1
    counter = 0
    tries = 0
    while before < counter or tries < 5:
        if before >= counter:
            tries += 1
        else:
            tries = 0
        before=counter
        try:
            for link in play_dynamic.collect_articles_links(page):
                href = link.get_attribute("href")
                if href in links_processed:
                    continue
                collect_item_data(link)
                links_processed.add(href)
                counter += 1
            print(f"scroll down: progress {counter}")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        except Exception as err:
            print(err)
        # time.sleep(3)
    print("all ", counter)