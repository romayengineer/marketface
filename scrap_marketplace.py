#!/usr/bin/env python3
import argparse
import time
from importlib import reload
# this is for quick development cycle as I reload this module
# dynamically and I update the code to see the changing without
# reloading the script or browser
import play_dynamic
from playwright.sync_api import sync_playwright

# Not used
field_email = 'xpath=//input[contains(@id, "email")]'
field_pass = 'xpath=//input[contains(@id, "pass")]'
button_login = 'xpath=//button[text()="Some text"]'

timeout = 3000

# Initialize parser
argParser = argparse.ArgumentParser()

# Adding optional argument
argParser.add_argument("-e", "--Email", help = "email to login")
argParser.add_argument("-p", "--Password", help = "password to login")
argParser.add_argument("-s", "--Show", help = "show browser? headless or not?")


# Read arguments from command line
args = argParser.parse_args()


if args.Show not in ("True", "False"):
    raise Exception("need to specify if headless or not, valid options True or False")


headless = False if args.Show == "True" else True

if not args.Email or not args.Password:
    raise Exception("need to pass login credentials, email and password")

def get_browser_context(p):
    browser = p.chromium.launch(headless=headless, slow_mo=200)
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
    # eval may use context and/or page so keep these arguments
    # these variables are used dynamically by eval
    email = args.Email
    passwd = args.Password
    help()
    while True:
        try:
            command = input(">>> ").strip()
            if command == "":
                continue
            reload(play_dynamic)
            # if command is a shortcut translate to code and execute
            command = play_dynamic.shortcuts.get(command, command)
            eval(command)
        except KeyboardInterrupt as err:
            print(err)
        except Exception as err:
            print(err)


links_processed = set()

def collect_item_data(link):
    href_full = link.get_attribute("href")
    href_short = play_dynamic.shorten_item_url(href_full)
    imgs = link.locator(play_dynamic.ximg).all()
    img_src = ""
    if len(imgs) > 0:
        img_src = imgs[0].get_attribute("src")
    file_name = play_dynamic.donwload_image(href_short, img_src)
    play_dynamic.create_item(href_short, file_name)

def collect_articles(page):
    counter = 0
    for link in play_dynamic.collect_articles_links(page, play_dynamic.xlinks):
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
    for link in play_dynamic.collect_articles_links(page, play_dynamic.xlinksall):
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
        page = new_page(context)
        play_repl(context, page)

if __name__ == "__main__":
    main()