import sys
sys.path.insert(0, "/home/marketface")

import time

from typing import List, cast

from playwright.sync_api import sync_playwright, Page

from marketface.data import backend, items
from marketface.data.errors import skip, url_not_unique, description_max_text, all_exceptions, playwright_timeout
from marketface.scrap_marketplace import email, password
from marketface.scrap_marketplace import get_browser_context
from marketface.page.facebook import FacebookPage, LoginCredentials, PageBlocked
from marketface.logger import getLogger


logger = getLogger("marketface.__main__")


def pull_articles(items_repo: items.ItemRepo, facebook: FacebookPage) -> None:
    for db_item in items_repo.get_incomplete():
        with skip(
            description_max_text,
            playwright_timeout,
            all_exceptions("get item incomplete")
        ):
            if db_item.url is None:
                continue
            facebook.market_item(
                db_item.url,
            ).market_details(
                item=db_item,
            )
            # when running pocketbase with --dev flag it logs the insert into query
            # db_item.log()
            items_repo.update(db_item)


def get_items_from_searches(items_repo: items.ItemRepo, facebook: FacebookPage, queries: List[str]) -> bool:
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
            max_tries = 6
            tries = 1
            while True:
                if links_counter_old < links_counter_new:
                    tries = 1
                else:
                    tries += 1
                    logger.info(
                        "scroll down '%s' %s %s %s",
                        query, tries, links_counter_old, links_counter_new,
                    )
                    time.sleep(5)
                if tries >= max_tries + 1:
                    break
                links_counter_old = links_counter_new
                with skip(playwright_timeout):
                    for href in facebook.get_market_href():
                        if href in links_processed_in_search:
                            continue
                        links_processed_in_search.add(href)
                        links_counter_new += 1
                        item = items.Item.model_validate({"url": href})
                        with skip(url_not_unique):
                            items_repo.create(item)
                cast(Page, facebook.current_page).evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
        except PageBlocked as err:
            logger.error(err)
            return False
        except Exception as err:
            logger.error("item search error on search '%s': %s", query, err)
    return True


def main() -> None:
    exit_success = True
    queries: List[str] = [
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
    with sync_playwright() as p:
        context = get_browser_context(p)
        facebook = FacebookPage(
            context=context,
            credentials=LoginCredentials(username=email, password=password),
        )
        facebook.login(timeout_ms=15000)
        pull_articles(items_repo, facebook)
        exit_success = get_items_from_searches(items_repo, facebook, queries)
        if exit_success:
            logger.info("main completed successfully")
        else:
            logger.error("main completed with an error")

if __name__ == "__main__":
    main()
