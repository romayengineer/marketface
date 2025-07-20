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