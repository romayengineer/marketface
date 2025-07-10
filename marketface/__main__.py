import os
import sys

from time import sleep
from typing import List, Optional

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/home/marketface")


from marketface import database
from marketface.play_dynamic import login, search, pull_articles, open_new_page, page_of_items
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.scrap_marketplace import collect_articles_all
from marketface.page.facebook import FacebookPage, LoginCredentials
from marketface.logger import getLogger


logger = getLogger("marketface.__main__")


def main() -> None:
    queries: List[str] = [
        # build search url for moto honda wave
        "moto honda",
        "honda wave",
        "moto honda wave",
        # build search url for apple with models, retina, pro, air
        "apple retina",
        "apple pro",
        "apple air",
        # build search url for apple with processors, i7, m1, m2, m3, m4
        "apple i7",
        "apple m1",
        "apple m2",
        "apple m3",
        "apple m4",
        # build search url for apple with memory ram, 16 gb, 32 gb
        "apple 16 gb",
        "apple 32 gb",
        # build search url for macbooks with models, retina, pro, air
        "macbook retina",
        "macbook pro",
        "macbook air",
        # build search url for macbooks with processors, i7, m1, m2, m3, m4
        "macbook i7",
        "macbook m1",
        "macbook m2",
        "macbook m3",
        "macbook m4",
        # build search url for macbooks with memory ram, 16 gb, 32 gb
        "macbook 16 gb",
        "macbook 32 gb",
    ]
    if not email or not password:
        raise ValueError(f"email and password are required for login")
    with sync_playwright() as p:
        context = get_browser_context(p)
        facebook = FacebookPage(
            context=context,
            credentials=LoginCredentials(username=email, password=password),
        )
        facebook.login(timeout_ms=10000)
        # TODO
        # 1. pull the data for the remaining articles links left on the db
        #    before pulling new ones
        # pull_articles(page, context)
        for db_item in page_of_items():
            try:
                item = facebook.market_item(
                    db_item.url
                ).market_details()
                if not item:
                    logger.error("could not get item details")
                    database.update_item_deleted(db_item.url)
                    continue
                item.log()
                database.update_item_by_url(db_item.url, item.to_dict())
            except Exception as err:
                logger.error(err)
        # 2. pull for new articles links
        for query in queries:
            try:
                facebook.market_search(
                    query=query
                )
                for href in facebook.get_market_href():
                    try:
                        item = facebook.market_item(
                            href
                        ).market_details()
                        if not item:
                            logger.error("could not get item details")
                            continue
                        item.log()
                        # TODO integrate with database save new items here
                    except:
                        pass
                # 3. save all new articles links from search page
                # collect_articles_all(page)
                # 4. pull the data from each of the new articles links
                # pull_articles(page, context)
            except Exception as err:
                print(err)

if __name__ == "__main__":
    main()
