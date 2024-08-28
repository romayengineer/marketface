"""
this is for quick development cycle as I reload this module
dynamically and I update the code to see the changing without
reloading the script or browser

once the functions in here are well developed and tested
I'll move them to the main script

the page object has all the methods supported and more:
page.click(
page.evaluate(
page.fill(
page.get_by_role(
page.goto(
page.is_visible(
page.locator(
page.set_default_timeout(
page.wait_for_timeout(
"""
import requests
import os.path

shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page)",
    "c": "play_dynamic.collect_articles(page)",
    "h": "play_dynamic.help()",
    "exit": "sys.exit(0)",
}

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
    s = "xpath=/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div[3]/div[1]/div[2]/div//a"
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
        file_name = f"data/{href_short[1:].replace("/", "_")}.jpg"
        if not os.path.isfile(file_name):
            image_bin = requests.get(img_src).content
            with open(file_name, "wb") as file:
                file.write(image_bin)
        counter += 1
    print("links: ", counter)

def login(page):
    page.goto("https://www.facebook.com")

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    login(page)