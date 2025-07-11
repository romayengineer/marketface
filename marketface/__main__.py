import sys
sys.path.insert(0, "/home/marketface")

from typing import List

from playwright.sync_api import sync_playwright

from marketface import database
from marketface.play_dynamic import page_of_items, create_item
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.page.facebook import FacebookPage, LoginCredentials, PageBlocked
from marketface.logger import getLogger


logger = getLogger("marketface.__main__")


def main() -> None:
    exit_with_error = False
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
                valid = True
                if item:
                    item.log()
                    if not item.title or not item.priceValid:
                        logger.error("item details error on data: '%s' '%s' '%s' '%s'", db_item.id, db_item.url, item.title, item.price)
                        valid = False
                else:
                    logger.error("item details error on item is None: '%s' '%s'", db_item.id, db_item.url)
                    valid = False
                if item and valid:
                    database.update_item_by_id(db_item.id, item.to_dict())
                    logger.info("item details updated: '%s' '%s'", db_item.id, db_item.url)
                else:
                    logger.warning("item details deleting: '%s' '%s'", db_item.id, db_item.url)
                    database.update_item_deleted_id(db_item.id)
            except Exception as err:
                logger.error("item details error on details: %s", err)
        # 2. pull for new articles links
        for query in queries:
            logger.info("searching with query '%s'", query)
            try:
                # TODO scroll down to get all items in search page
                # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                market_page = facebook.market_search(
                    query=query
                )
                if not market_page.valid_page:
                    logger.error("invalid page '%s'", query)
                for href in facebook.get_market_href():
                    try:
                        model = create_item(href)
                        if model:
                            logger.info("item search created: '%s' '%s'", query, href)
                    except Exception as err:
                        logger.error("item search error on create '%s' '%s': %s", query, href, err)
                # 3. save all new articles links from search page
                # collect_articles_all(page)
                # 4. pull the data from each of the new articles links
                # pull_articles(page, context)
            except PageBlocked as err:
                logger.error(err)
                exit_with_error = True
                break
            except Exception as err:
                logger.error("item search error on search '%s': %s", query, err)
        if exit_with_error:
            logger.info("main completed with an error")
        else:
            logger.info("main completed successfully")

if __name__ == "__main__":
    main()
