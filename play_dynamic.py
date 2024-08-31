import time
import requests
import os.path
import database
from importlib import reload
from playwright.sync_api import TimeoutError
from pocketbase.utils import ClientResponseError
from contextlib import contextmanager

reload(database)

shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page)",
    "c": "play_dynamic.collect_articles(page)",
    "p": "play_dynamic.pull_articles(page, context)",
    "h": "play_dynamic.help()",
    "exit": "sys.exit(0)",
}

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div"
xdetails = "/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/div[1]"
xtitle = f"xpath={xbase}{xdetails}/div[1]/h1/span"
xprice = f"xpath={xbase}{xdetails}/div[1]/div[1]/div/span"
xdesc = f"xpath={xbase}{xdetails}/div[5]/div/div[2]/div[1]"

lowercase = [chr(n) for n in range(ord('a'), ord('a') + 26)]
uppercase = [chr(n) for n in range(ord('A'), ord('A') + 26)]
letters = lowercase + uppercase
numbers = [str(n) for n in range(10)]
especial = [" ", "'", '"', ".", ",", ";", "!", "?", "_", "-"]
alphabet = letters + numbers + especial

def help():
    print("Getting started tutorial:")
    print("")
    print("1. run `l` this will load facebook's login page")
    print("   login as usual with your user and password")
    print("2. run `s` to open the marketplace and search")
    print("   by default it searchs for a macbook")
    print("3. run `c` to collect the marketplace items")
    print("   from the marketplace search page")
    print("")
    for shortcut, command in shortcuts.items():
        print(shortcut, " --> ", command)

def div_by_aria_label(page, label):
    return page.locator(f"css=div[aria-label='{label}']")

def collect_articles_links(page):
    # TODO check why am I getting less items that there actually are
    # I am getting a few less like 4 less items it's related to the
    # selector probably
    print("collect articles links")
    s = f"xpath={xbase}/div[3]/div[1]/div[2]/div//a"
    collections = page.locator(s).all()
    for coll in collections:
        href = coll.get_attribute('href')
        if not href.startswith("/marketplace/item/"):
            continue
        yield coll

def shorten_item_url(url):
    """
    Turns the url to the following format
    /marketplace/item/<number>
    """
    start = "/marketplace/item/"
    if not url.startswith(start):
        return url
    i = len(start)
    u = len(url)
    if not u > i:
        return url
    str_numbers = [str(n) for n in range(10)]
    while i < u:
        if url[i] not in str_numbers:
            break
        i += 1
    shortened = url[:i]
    if shortened[-1] not in str_numbers:
        raise Exception("marketplace item url does not have an id")
    return shortened

def create_item(href_short, file_name):
    try:
        database.get_item_by_url(href_short)
    except ClientResponseError:
        print("record doesn't exist... creating it")
        database.create_item(href_short, file_name)

def donwload_image(href_short, img_src):
    file_name = f"data/images/{href_short[1:].replace("/", "_")}.jpg"
    if not os.path.isfile(file_name):
        image_bin = requests.get(img_src).content
        with open(file_name, "wb") as file:
            file.write(image_bin)
    return file_name

def collect_articles(page):
    counter = 0
    for link in collect_articles_links(page):
        href_full = link.get_attribute("href")
        href_short = shorten_item_url(href_full)
        imgs = link.locator("xpath=//img").all()
        img_src = ""
        if len(imgs) > 0:
            img_src = imgs[0].get_attribute("src")
        print("href: ", href_short, img_src)
        file_name = donwload_image(href_short, img_src)
        create_item(href_short, file_name)
        counter += 1
    print("links: ", counter)

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

def get_item_page_details(page):
    # TODO save into pocketbase
    title = ""
    description = ""
    price = ""
    with if_error_print_and_continue():
        title = oneline(page.locator(xtitle).text_content())
        price = oneline(page.locator(xprice).text_content())
        description = oneline(page.locator(xdesc).text_content())
    print("title: ", title)
    print("price: ", price)
    print("description: ", description)

def page_of_items(pages=10):
    page = 1
    while True:
        items = database.get_items_incomplete(page, pages).items
        if not items:
            break
        for item in items:
            yield item
        inp = input("Continue? (Y/n): ")
        if inp != "y" and inp != "":
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
    #TODO remove pages=1 is just for testing and get only one
    for item in page_of_items(pages=1):
        new_page = context.new_page()
        new_url = f"https://www.facebook.com{item.url}"
        print("new_url: ", new_url)
        try:
            new_page.goto(new_url)
        except TimeoutError as err:
            print("TimeoutError: ", err)
        time.sleep(2)
        get_item_page_details(new_page)
        new_page.close()
        time.sleep(2)


def login(page):
    page.goto("https://www.facebook.com")

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    login(page)