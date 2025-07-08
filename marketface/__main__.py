import os
import sys

from time import sleep
from typing import List

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/home/marketface")


from marketface.play_dynamic import login, search, pull_articles
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context, new_page
from marketface.scrap_marketplace import collect_articles_all


def get_url_for_query(query: str) -> str:
    # "%20" means space so "macbook%2032"
    newQuery = query.replace(" ", "%20")
    return f"https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query={newQuery}&exact=false"


def main() -> None:
    urls: List[str] = [
        # search apple for specific models, retina, pro, air
        get_url_for_query("apple retina"),
        get_url_for_query("apple pro"),
        get_url_for_query("apple air"),
        # search apple for specific processors i7, m1, m2, m3, m4
        get_url_for_query("apple i7"),
        get_url_for_query("apple m1"),
        get_url_for_query("apple m2"),
        get_url_for_query("apple m3"),
        get_url_for_query("apple m4"),
        # search apple for specific memories 16 gb, 32 gb
        get_url_for_query("apple 16 gb"),
        get_url_for_query("apple 32 gb"),
        # search macbooks for specific models, retina, pro, air
        get_url_for_query("macbook retina"),
        get_url_for_query("macbook pro"),
        get_url_for_query("macbook air"),
        # search macbooks for specific processors i7, m1, m2, m3, m4
        get_url_for_query("macbook i7"),
        get_url_for_query("macbook m1"),
        get_url_for_query("macbook m2"),
        get_url_for_query("macbook m3"),
        get_url_for_query("macbook m4"),
        # search macbooks for specific memories 16 gb, 32 gb
        get_url_for_query("macbook 16 gb"),
        get_url_for_query("macbook 32 gb"),
    ]
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = new_page(context)
        login(page, email, password)
        # first pull the publication links from each search page
        for url in urls:
            try:
                print(f"SEARCH: {url}")
                search(page, url)
                collect_articles_all(page)
                # then pull the data from each of the publication links
                pull_articles(page, context)
            except Exception as err:
                print(err)

if __name__ == "__main__":
    main()
