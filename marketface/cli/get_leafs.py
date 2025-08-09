#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

from marketface.data.backend import auth
from marketface.data.items import ItemRepo
from marketface.logger import getLogger
from marketface.page import cleanse
from random import randint
from bs4 import BeautifulSoup


logger = getLogger("get_leafs")


def main() -> None:
    client = auth()

    items_repo = ItemRepo(client)

    count = 1
    max_count = 30
    while True:
        for item in items_repo.all({"filter": "html != ''"}):
            # to get random samples
            if randint(0, 10) != 0:
                continue
            print("URL: ", item.url)
            html = str(item.html)
            soup = BeautifulSoup(html, 'html.parser')
            lines = []
            for text in soup._all_strings(strip=True):
                if text == "Publicidad":
                    break
                if text in cleanse.text_to_skip:
                    continue
                lines.append(text)
            print(" |\n".join(lines))
            print("-" * 80)
            print("-" * 80)
            count += 1
            if count >= max_count:
                return


if __name__ == "__main__":
    main()
