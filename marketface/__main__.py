import sys
sys.path.insert(0, "/home/marketface")

import time

from typing import List, cast

from playwright.sync_api import sync_playwright, Page

from marketface.data import backend, items
from marketface.play_dynamic import create_item
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.page.facebook import FacebookPage, LoginCredentials, PageBlocked
from marketface.logger import getLogger

from pocketbase.utils import ClientResponseError


logger = getLogger("marketface.__main__")


def pull_articles(items_repo: items.ItemRepo, facebook: FacebookPage) -> None:
    for db_item in items_repo.get_incomplete():
        try:
            if db_item.url is None:
                continue
            item = facebook.market_item(
                db_item.url
            ).market_details()
            valid = True
            if item:
                if not item.title:
                    logger.error("item details error on data: '%s' '%s' '%s' '%s'", db_item.id, db_item.url, item.title, item.price)
                    valid = False
            else:
                logger.error("item details error on item is None: '%s' '%s'", db_item.id, db_item.url)
                valid = False
            if item:
                db_item.title = item.title
                db_item.priceStr = item.priceStr
                db_item.description = item.description
                db_item.priceUsd = item.priceUsd
                db_item.priceArs = item.priceArs
                db_item.usd = item.usd
                db_item.log()
            if valid:
                db_item.deleted = False
                items_repo.update(db_item)
                # database.update_item_by_id(db_item.id, item.to_dict())
                logger.info("item details updated: '%s' '%s'", db_item.id, db_item.url)
            else:
                db_item.deleted = True
                items_repo.update(db_item)
                # database.update_item_deleted_id(db_item.id)
                logger.warning("item details deleting: '%s' '%s'", db_item.id, db_item.url)
        except ClientResponseError as err:
            if err.status == 400:
                code = err.data.get("data", {}).get("description", {}).get("code")
                error_code = "validation_max_text_constraint"
                if code == error_code:
                    logger.warning(error_code)
                    continue
            logger.error("item details error on details: %s", err)
        except Exception as err:
            # import pdb; pdb.set_trace()
            logger.error("item details error on details: %s", err)


def get_items_from_searches(facebook: FacebookPage, queries: List[str]) -> bool:
    for query in queries:
        logger.info("searching with query '%s'", query)
        try:
            market_page = facebook.market_search(
                query=query
            )
            if not market_page.valid_page:
                logger.warning("invalid page '%s'", query)
            links_processed_in_search = set()
            links_counter_old = -1
            links_counter_new = 0
            max_tries = 10
            while True:
                if links_counter_old < links_counter_new:
                    tries = 1
                else:
                    tries += 1
                if tries >= max_tries + 1:
                    break
                links_counter_old = links_counter_new
                try:
                    for href in facebook.get_market_href():
                        if href in links_processed_in_search:
                            continue
                        links_processed_in_search.add(href)
                        links_counter_new += 1
                        try:
                            model = create_item(href)
                            if model:
                                logger.info("item search created: '%s' '%s'", query, href)
                        except Exception as err:
                            logger.error("item search error on create '%s' '%s': %s", query, href, err)
                except Exception as err:
                    logger.error("item search error on get href '%s': %s", query, err)
                # page is defined
                logger.info("scroll down %s %s %s", tries, links_counter_old, links_counter_new)
                cast(Page, facebook.current_page).evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            # 3. save all new articles links from search page
            # collect_articles_all(page)
            # 4. pull the data from each of the new articles links
            # pull_articles(page, context)
        except PageBlocked as err:
            logger.error(err)
            # exit_with_error = True
            return False
        except Exception as err:
            logger.error("item search error on search '%s': %s", query, err)
    return True


def main() -> None:
    exit_success = True
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
    client = backend.auth()
    items_repo = items.ItemRepo(client)
    items_repo.create_table()
    # sys.exit(0)
    with sync_playwright() as p:
        context = get_browser_context(p)
        facebook = FacebookPage(
            context=context,
            credentials=LoginCredentials(username=email, password=password),
        )
        facebook.login(timeout_ms=15000)
        # TODO
        # 1. pull the data for the remaining articles links left on the db
        #    before pulling new ones
        # pull_articles(page, context)
        pull_articles(items_repo, facebook)
        # 2. pull for new articles links
        exit_success = get_items_from_searches(facebook, queries)
        if exit_success:
            logger.info("main completed successfully")
        else:
            logger.error("main completed with an error")

if __name__ == "__main__":
    main()
