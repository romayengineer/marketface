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
    "v": "play_dynamic.collect_articles_all(page)",
    "p": "play_dynamic.pull_articles(page, context)",
    "h": "play_dynamic.help()",
    "exit": "sys.exit(0)",
}

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div"
xdetails = "/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/div[1]"
# these are all the xpath being used in this script
xtitle = f"xpath={xbase}{xdetails}/div[1]/h1/span"
xprice = f"xpath={xbase}{xdetails}/div[1]/div[1]/div/span"
xdesc = f"xpath={xbase}{xdetails}/div[5]/div/div[2]/div[1]"
xlinks = f"xpath={xbase}/div[3]/div[1]/div[2]/div//a"
xlinksall = f"xpath={xbase}/div[3]//a"
ximg = "xpath=//img"

lowercase = [chr(n) for n in range(ord('a'), ord('a') + 26)] + ["ñ"] # Spanish letter
uppercase = [chr(n) for n in range(ord('A'), ord('A') + 26)] + ["Ñ"]
letters = lowercase + uppercase
numbers = [str(n) for n in range(10)]
especial = [" ", "’", "'", '"', ".", ",", ";", "!", "?", "_", "-", "/", "\\", "|", "(", ")", "[", "]", "{", "}"]
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

def collect_articles_links(page, xpath):
    # TODO check why am I getting less items that there actually are
    # I am getting a few less like 4 less items it's related to the
    # selector probably
    # print("collect articles links")
    collections = page.locator(xpath).all()
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
        print("href_short: ", href_short)
        database.create_item(href_short, file_name)

def donwload_image(href_short, img_src):
    file_name = f"data/images/{href_short[1:].replace("/", "_")}.jpg"
    if not os.path.isfile(file_name):
        image_bin = requests.get(img_src).content
        with open(file_name, "wb") as file:
            file.write(image_bin)
    return file_name

def collect_item_data(link):
    href_full = link.get_attribute("href")
    href_short = shorten_item_url(href_full)
    imgs = link.locator(ximg).all()
    img_src = ""
    if len(imgs) > 0:
        img_src = imgs[0].get_attribute("src")
    file_name = donwload_image(href_short, img_src)
    create_item(href_short, file_name)

def collect_articles(page):
    counter = 0
    for link in collect_articles_links(page, xlinks):
        collect_item_data(link)
        counter += 1
    print("first ", counter)

def collect_articles_all(page):
    # collects all articles including the ones
    # from outside your search
    counter = 0
    for link in collect_articles_links(page, xlinksall):
        collect_item_data(link)
        counter += 1
    print("all ", counter)

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

def get_item_page_details(url, page):
    # TODO save into pocketbase
    title = ""
    description = ""
    priceStr = ""
    price = "" # price without currency
    priceArs = 0 # price in Argentinian Pesos
    priceUsd = 0 # price in Dollars
    isUsd = False
    #TODO update this rate put it somewhere else
    # exchange rate of 2024-08-31
    usdArsRate = 1350.00
    with if_error_print_and_continue():
        title = oneline(page.locator(xtitle).text_content())
        priceStr = oneline(page.locator(xprice).text_content())
        description = oneline(page.locator(xdesc).text_content())
    print("title: ", title)
    print("price: ", priceStr)
    print("description: ", description)
    # if you are in a different location change this rate convertion logic
    if priceStr and priceStr.startswith("ARS"):
        # remove first 3 characters from ARS
        # so far nobody use cents but if they do this will fail
        # conver to float in that case
        price = priceStr.partition(" ")[0][3:].replace(",", "")
    elif priceStr and priceStr[0] in numbers:
        price = priceStr.partition(" ")[0].replace(",", "")
    else:
        database.update_item_deleted(url)
        print("Currency must be in ARS! marked as deleted!")
        return
    # somethimes the price is followed by a scratched old price
    # the text_content puts this text on the same word meaning
    # it is not separaated by an space in that case only
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
    print("priceUsd: ", priceUsd)
    print("priceArs: ", priceArs)
    print("isUsd: ", isUsd)
    database.update_item_by_url(
        url, title,
        priceArs, priceUsd, usdArsRate,
        isUsd,
        description
    )

def page_of_items(pages=100):
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
    for item in page_of_items():
        new_page = context.new_page()
        new_url = f"https://www.facebook.com{item.url}"
        print("new_url: ", new_url)
        try:
            new_page.goto(new_url)
        except TimeoutError as err:
            print("TimeoutError: ", err)
        time.sleep(2)
        get_item_page_details(item.url, new_page)
        new_page.close()
        time.sleep(2)


def login(page):
    page.goto("https://www.facebook.com")

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    login(page)