#!/usr/bin/env python3
import argparse
import os
import sys
import time
from argparse import ArgumentTypeError
from importlib import reload

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.getcwd())

# this is for quick development cycle as I reload this module
# dynamically and I update the code to see the changing without
# reloading the script or browser
from marketface import play_dynamic
from marketface.utils import shorten_item_url
from marketface.creds import read_creds

# Not used
field_email = 'xpath=//input[contains(@id, "email")]'
field_pass = 'xpath=//input[contains(@id, "pass")]'
button_login = 'xpath=//button[text()="Some text"]'

timeout = 3000

# Initialize parser
argParser = argparse.ArgumentParser()

# Adding optional argument
argParser.add_argument("-e", "--Email", help="email to login")
argParser.add_argument("-p", "--Password", help="password to login")
argParser.add_argument(
    "-s", "--Show",
    type=bool,
    default=True,
    help="show browser? headless or not?"
)


# Read arguments from command line
args = argParser.parse_args()

headless = not args.Show

creds = read_creds(os.path.join(os.getcwd(), "creds.json"))

email = args.Email or creds.get("email")
password = args.Password or creds.get("password")

if not email or not password:
    raise ArgumentTypeError("need to pass login credentials, email and password")

storage_state_file="browser_context.json"

def get_browser_context(p):
    browser = p.chromium.launch(headless=headless, slow_mo=200)
    context = browser.new_context(storage_state=storage_state_file)
    print("New Browser")
    return context


def new_page(context):
    page = context.new_page()
    page.set_default_timeout(timeout)
    time.sleep(3)
    print("New Page")
    return page


def play_repl(context, page):
    # eval may use context and/or page so keep these arguments
    # these variables are used dynamically by eval
    passwd = password  # noqa
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


links_processed = set()


def collect_item_data(link):
    href_full = link.get_attribute("href")
    href_short = shorten_item_url(href_full)
    href_full = "https://www.facebook.com" + href_short
    imgs = link.locator(play_dynamic.ximg).all()
    img_src = imgs[0].get_attribute("src") if len(imgs) > 0 else ""
    file_name = play_dynamic.download_image(href_short, img_src)
    play_dynamic.create_item(href_full, file_name)


def collect_articles(page):
    counter = 0
    for link in play_dynamic.collect_articles_links(page):
        href = link.get_attribute("href")
        if href in links_processed:
            counter += 1
            continue
        collect_item_data(link)
        links_processed.add(href)
        counter += 1
    print("first ", counter)


def collect_articles_all(page):
    # collects all articles including the ones
    # from outside your search
    counter = 0
    for link in play_dynamic.collect_articles_links(page):
        href = link.get_attribute("href")
        if href in links_processed:
            counter += 1
            continue
        collect_item_data(link)
        links_processed.add(href)
        counter += 1
    print("all ", counter)


def main():
    with sync_playwright() as p:
        context = get_browser_context(p)
        try:
            page = new_page(context)
            play_repl(context, page)
        finally:
            print("saving browser context")
            context.storage_state(path=storage_state_file)


if __name__ == "__main__":
    main()
