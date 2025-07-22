#!/usr/bin/env python3
from marketface.data.backend import auth
from marketface.data.items import ItemRepo
from marketface.logger import getLogger
from marketface.page import cleanse
from random import randint
from bs4 import BeautifulSoup


logger = getLogger("get_leafs")

logger.info = print

def main() -> None:
    client = auth()

    items_repo = ItemRepo(client)

    count = 1
    max_count = 10
    while True:
        for item in items_repo.all({"filter": "html != ''"}):
            if randint(0, 100) != 0:
                continue
            print("URL: ", item.url)
            html = str(item.html)
            # for leaf in cleanse.get_parent_tags(html):
            #     logger.info(leaf.get_text(separator=" | ", strip=True))
            soup = BeautifulSoup(html, 'html.parser')
            # logger.info(soup.get_text(separator=" |\n", strip=True))
            text_to_skip = [
                "Compartir",
                "Guardar",
                "Enviar",
                "Enviar mensaje",
                "Envía un mensaje al vendedor",
                "Hola. ¿Sigue disponible?",
                "Hola. ¿Sigue estando disponible?",
                "Detalles del vendedor",
            ]
            lines = []
            for text in soup._all_strings(strip=True):
                if text == "Publicidad":
                    break
                if text in text_to_skip:
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
