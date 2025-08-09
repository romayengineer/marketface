#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

from marketface.data.backend import auth
from marketface.data.items import ItemRepo, Item
from marketface.logger import getLogger
from marketface.page import cleanse
from random import randint
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Iterable, Optional, Set
from itertools import islice


logger = getLogger("get_leafs")


@dataclass
class IterFilter:
    break_on: Set[str]
    continue_on: Set[str]


@dataclass
class HtmlParser:
    item: Item
    parsed: BeautifulSoup
    ifilter: Optional[IterFilter] = None
    text: Optional[str] = None


def should_skip(size: int) -> bool:
    # to get random samples
    if randint(0, size) == 0:
        return False
    return True


def ifilter(condition: IterFilter, texts: Iterable[str]) -> Iterable[str]:
    for text in texts:
        if text in condition.break_on:
            return
        if text in condition.continue_on:
            continue
        yield text


def list_html_not_empty(item_repo: ItemRepo) -> Iterable[Item]:
    for item in item_repo.all({"filter": "html != ''"}):
        yield item


def to_html_object(item: Item) -> Optional[BeautifulSoup]:
    if not item.html:
        return
    return BeautifulSoup(item.html, 'html.parser')


def parse(item: Item) -> Optional[BeautifulSoup]:
    return to_html_object(item)


def new_parser(item: Item, ifilter: Optional[IterFilter] = None) -> Optional[HtmlParser]:
    parsed = parse(item)
    if not parsed:
        return
    parser = HtmlParser(
        item=item,
        parsed=parsed,
        ifilter=ifilter,
    )
    return parser


def all_strings(parser: HtmlParser) -> Iterable[str]:
    for text in parser.parsed._all_strings(strip=True):
        yield text


def print_sep(symb: str = "-", leng: int = 80) -> None:
    print(symb * leng)
    print(symb * leng)


def print_all(itera: Iterable) -> None:
    for string in itera:
        print(string)


def filter_random(itera: Iterable, times: int = 2) -> Iterable:
    for i in itera:
        if should_skip(times):
            continue
        yield i


def print_text(parser: HtmlParser) -> None:
    strings = all_strings(parser)
    if parser.ifilter:
        strings = ifilter(parser.ifilter, strings)
    print_all(strings)
    print_sep()


def get_text_and_print_random() -> None:

    client = auth()

    items_repo = ItemRepo(client)

    take = 5

    ifilter = IterFilter(
        break_on={"Publicidad",},
        continue_on=cleanse.text_to_skip,
    )

    for item in islice(filter_random(list_html_not_empty(items_repo)), take):
        parser = new_parser(item=item, ifilter=ifilter)
        if not parser:
            continue
        print_text(parser)


def main() -> None:
    get_text_and_print_random()


if __name__ == "__main__":
    main()
