from bs4 import BeautifulSoup
from bs4.element import Tag

from typing import Set, List, cast


def clean_html_attributes(html_content: str, unwanted_attrs: Set[str]) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in cast(List[Tag], soup.find_all(True)):
        for attr in list(tag.attrs.keys()):
            if attr in unwanted_attrs:
                del tag[attr]
    return str(soup)