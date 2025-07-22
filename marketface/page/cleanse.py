from bs4 import BeautifulSoup
from bs4.element import Tag
from bs4._typing import _OneElement

from typing import Set, List, Iterator, Optional, cast


text_to_skip = [
    "Compartir",
    "Guardar",
    "Enviar",
    "Enviar mensaje",
    "Envía un mensaje al vendedor",
    "Hola. ¿Sigue disponible?",
    "Hola. ¿Sigue estando disponible?",
    "Detalles del vendedor",
    "Publicidad",
]


def clean_html_attributes(html_content: str, unwanted_attrs: Set[str]) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in cast(List[Tag], soup.find_all(True)):
        for attr in list(tag.attrs.keys()):
            if attr in unwanted_attrs:
                del tag[attr]
    return str(soup)

def is_leaf(tag: Tag) -> bool:
    return tag.find(True, recursive=False) is None

def has_text(tag: Tag) -> bool:
    for _ in tag._all_strings(strip=True):
        return True
    return False

def get_parent(tag: _OneElement, up: int = 1) -> _OneElement:
    if up > 0 and tag.parent:
        return get_parent(tag.parent, up = up - 1)
    return tag

def get_leaf_tags(html_content: str) -> Iterator[_OneElement]:
    soup = BeautifulSoup(html_content, 'html.parser')
    for leaf in soup.find_all(lambda tag: is_leaf(tag) and has_text(tag)):
        yield leaf

def get_parent_tags(html_content: str, up: int = 2) -> Iterator[_OneElement]:
    soup = BeautifulSoup(html_content, 'html.parser')
    for leaf in soup.find_all(lambda tag: is_leaf(tag) and has_text(tag)):
        parent = get_parent(leaf, up=up)
        text = parent.get_text(separator=" | ", strip=True)
        if any(map(
            lambda m: m in text,
            [
                "Envía un mensaje al vendedor",
                "Hola. ¿Sigue disponible?",
                "Hola. ¿Sigue estando disponible?",
                "Más información",
            ])):
                continue
        yield parent
