import os
import sys

from time import sleep
from typing import List, Optional

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/home/marketface")


from marketface.play_dynamic import login, search, pull_articles, open_new_page
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.scrap_marketplace import collect_articles_all


def get_url_for_query(query: str, min_price: Optional[int] = None) -> str:
    # "%20" means space so "macbook%2032"
    newQuery = query.replace(" ", "%20")
    minPrice = ""
    if min_price:
        minPrice = f"&minPrice={min_price}"
    return f"https://www.facebook.com/marketplace/buenosaires/search?query={newQuery}&exact=false{minPrice}"


def main() -> None:
    urls: List[str] = [
        # build search url for moto honda wave
        get_url_for_query("moto honda"),
        get_url_for_query("honda wave"),
        get_url_for_query("moto honda wave"),
        # build search url for apple with models, retina, pro, air
        get_url_for_query("apple retina"),
        get_url_for_query("apple pro"),
        get_url_for_query("apple air"),
        # build search url for apple with processors, i7, m1, m2, m3, m4
        get_url_for_query("apple i7"),
        get_url_for_query("apple m1"),
        get_url_for_query("apple m2"),
        get_url_for_query("apple m3"),
        get_url_for_query("apple m4"),
        # build search url for apple with memory ram, 16 gb, 32 gb
        get_url_for_query("apple 16 gb"),
        get_url_for_query("apple 32 gb"),
        # build search url for macbooks with models, retina, pro, air
        get_url_for_query("macbook retina"),
        get_url_for_query("macbook pro"),
        get_url_for_query("macbook air"),
        # build search url for macbooks with processors, i7, m1, m2, m3, m4
        get_url_for_query("macbook i7"),
        get_url_for_query("macbook m1"),
        get_url_for_query("macbook m2"),
        get_url_for_query("macbook m3"),
        get_url_for_query("macbook m4"),
        # build search url for macbooks with memory ram, 16 gb, 32 gb
        get_url_for_query("macbook 16 gb"),
        get_url_for_query("macbook 32 gb"),
    ]
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = open_new_page(context)
        login(page, email, password)
        # 1. pull the data for the remaining articles links left on the db
        #    before pulling new ones
        pull_articles(page, context)
        # 2. pull for new articles links
        for url in urls:
            try:
                print(f"SEARCH: {url}")
                search(page, url)
                # 3. save all new articles links from search page
                collect_articles_all(page)
                # 4. pull the data from each of the new articles links
                pull_articles(page, context)
            except Exception as err:
                print(err)

if __name__ == "__main__":
    main()
