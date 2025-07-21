#!/usr/bin/env python3
from marketface.data.backend import auth
from marketface.data.items import ItemRepo
from marketface.logger import getLogger
from marketface.page.cleanse import get_leaf_tags
from random import randint


logger = getLogger("get_leafs")

logger.info = print

def main() -> None:
    client = auth()

    items_repo = ItemRepo(client)
    while True:
        for item in items_repo.all({"filter": "html != ''"}):
            if randint(0, 100) != 50:
                continue
            logger.info("URL: %s", item.url)
            html = str(item.html)
            for leaf in get_leaf_tags(html):
                logger.info(leaf)
            return


if __name__ == "__main__":
    main()
