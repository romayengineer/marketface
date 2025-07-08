import os
import sys

from time import sleep

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/home/marketface")


from marketface.play_dynamic import login, search, pull_articles
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context, new_page
from marketface.scrap_marketplace import collect_articles_all


def main() -> None:
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = new_page(context)
        login(page, email, password)
        search(page)
        collect_articles_all(page)
        pull_articles(page, context)

if __name__ == "__main__":
    main()
