from bs4 import BeautifulSoup
from bs4.element import Tag

from typing import Set, List, Iterator, cast


def clean_html_attributes(html_content: str, unwanted_attrs: Set[str]) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in cast(List[Tag], soup.find_all(True)):
        for attr in list(tag.attrs.keys()):
            if attr in unwanted_attrs:
                del tag[attr]
    return str(soup)

def is_leaf(tag: Tag) -> bool:
    return tag.find(True, recursive=False) is None

def get_leaf_tags(html_content: str) -> Iterator[Tag]:
    soup = BeautifulSoup(html_content, 'html.parser')
    for leaf in soup.find_all(is_leaf):
        yield cast(Tag, leaf)
