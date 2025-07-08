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
    return f"https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query={query}&exact=false"


def main() -> None:
    # "%20" means space so "macbook%2032"
    urls: List[str] = [
        # search macbooks for specific processors i7, m1, m2, m3, m4
        get_url_for_query("macbook%20i7"),
        get_url_for_query("macbook%20m1"),
        get_url_for_query("macbook%20m2"),
        get_url_for_query("macbook%20m3"),
        get_url_for_query("macbook%20m4"),
        # search macbooks for specific memories 16 gb, 32 gb
        get_url_for_query("macbook%2016"),
        get_url_for_query("macbook%2032"),
    ]
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = new_page(context)
        login(page, email, password)
        # first pull the publication links from each search page
        for url in urls:
            search(page, url)
            collect_articles_all(page)
        # then pull the data from each of the publication links
        pull_articles(page, context)

if __name__ == "__main__":
    main()
