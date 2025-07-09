"""
the xpaths for the price and description changed and the locator selector is throwing an error
this script is to test that out and fix, there ar new xprice1 and xprice2 xpaths to use the same
for the description
"""
import os
import sys

from time import sleep
from typing import List, Optional

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/home/marketface")


from marketface.play_dynamic import login, open_article_page, open_new_page
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.scrap_marketplace import collect_articles_all

# common xpath that is used in all other xpaths
xbase = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]"
xtitle = f"xpath={xbase}/div[1]/div[1]/h1"
xprice1 = f"xpath={xbase}/div[1]/div[1]/div[1]"
xprice2 = f"xpath={xbase}/div[1]/div[2]"
xdesc1 = f"xpath={xbase}/div[1]/div[5]/div/div[2]/div[1]"
xdesc2 = f"xpath={xbase}/div[5]"



def get_url_for_query(query: str, min_price: Optional[int] = None) -> str:
    # "%20" means space so "macbook%2032"
    newQuery = query.replace(" ", "%20")
    minPrice = ""
    if min_price:
        minPrice = f"&minPrice={min_price}"
    return f"https://www.facebook.com/marketplace/buenosaires/search?query={newQuery}&exact=false{minPrice}"


def main() -> None:
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        # page = open_new_page(context)
        # login(page, email, password)
        # error_url = "https://www.facebook.com/marketplace/item/1591032414860845"
        # error_url = "https://www.facebook.com/marketplace/item/3946724162140505"
        error_url = "https://www.facebook.com/marketplace/item/651361191023356"
        # this function fails on the selector waits and times out
        # open_article_page(context, error_url)
        new_page = open_new_page(context)
        new_page.goto(error_url, timeout=10000)
        # import pdb; pdb.set_trace()
        title = new_page.locator(xtitle).text_content()
        print(f"title: {title}")
        priceStr = new_page.locator(xprice1).text_content()
        print(f"priceStr: {priceStr}")
        description = new_page.locator(xdesc1).text_content()
        print(f"description: {description}")
        new_page.close()

if __name__ == "__main__":
    main()
