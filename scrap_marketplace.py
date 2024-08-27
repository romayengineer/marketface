#!/usr/bin/env python3
import sys
import time
from playwright.sync_api import sync_playwright

timeout = 3000

def get_browser_context(p):
    browser = p.chromium.launch(headless=False, slow_mo=200)
    context = browser.new_context(storage_state="browser_context.json")
    print("New Browser")
    return context

def new_page(context):
    page = context.new_page()
    page.set_default_timeout(timeout)
    time.sleep(3)
    print("New Page")
    return page


def play_repl(context, page):
    while True:
        try:
            command = input(">>> ")
            if command == "exit":
                sys.exit(0)
            eval(command)
        except Exception as err:
            print(err)

def main():
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = new_page(context)
        play_repl(context, page)


if __name__ == "__main__":
    main()