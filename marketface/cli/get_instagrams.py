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
from typing import Set


logger = getLogger("get_leafs")


def main() -> Set:
    client = auth()

    items_repo = ItemRepo(client)

    accounts = set()
    for item in items_repo.all({"filter": "html ~ '@'"}):
        html = str(item.html)
        soup = BeautifulSoup(html, 'html.parser')
        for text in soup._all_strings(strip=True):
            try:
                i = text.index("@")
                account = text[i:i+20].split("\n", 1)[0].strip().lower()
                if account not in accounts:
                    accounts.add(account)
            except ValueError:
                # index not found
                pass
    return accounts


if __name__ == "__main__":
    accounts = main()
    print("\n".join(accounts))
