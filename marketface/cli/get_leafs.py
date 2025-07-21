#!/usr/bin/env python3
from marketface.data.backend import auth
from marketface.data.items import ItemRepo
from marketface.logger import getLogger
from marketface.page.cleanse import get_leaf_tags


logger = getLogger("get_leafs")


def main() -> None:
    client = auth()

    items_repo = ItemRepo(client)
    for item in items_repo.all({"filter": "html != ''"}):
        logger.info("URL: %s", item.url)
        html = str(item.html)
        for leaf in get_leaf_tags(html):
            logger.info(leaf)
        break


if __name__ == "__main__":
    main()
