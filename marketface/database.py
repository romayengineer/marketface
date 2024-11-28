from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import URL, Connection, Engine, Row, create_engine, text, util

DB_DRIVERNAME = "postgresql"
DB_USERNAME = "postgres"
DB_PASSWORD = "password"
DB_HOST = "marketface-postgresql"
DB_PORT = 5432
DB_NAME = "marketface"

DATABASE_URL = URL(
    drivername=DB_DRIVERNAME,
    username=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query=util.immutabledict(),
)


def get_engine(database_url: str | URL = DATABASE_URL) -> Engine:
    return create_engine(database_url)


def get_connection(database_url: str | URL = DATABASE_URL) -> Connection:
    return get_engine(database_url).connect()


class ItemsTable:

    def __init__(self, conn: Connection):
        self.conn = conn

    def get_first_item(self, query_filter: str) -> Optional[Row]:
        return self.conn.execute(
            text(f"select * from items where {query_filter} limit 1")
        ).fetchone()

    def get_item_by_url(self, url: str) -> Optional[Row]:
        return self.get_first_item(f"url = '{url}'")

    def get_items_list(self, start: int, count: int, filter: str) -> Sequence[Row]:
        return self.conn.execute(
            text(f"select * from items where {filter} limit {count} offset {start}")
        ).fetchall()

    def get_items_list_all(self, start: int, count: int, filter: str) -> Sequence[Row]:
        items: List[Row] = []
        while True:
            new_items = self.get_items_list(start, count, filter)
            if not new_items:
                break
            items.extend(new_items)
            start += count
        return items

    def get_items_incomplete(self, start: int, count: int) -> Sequence[Row]:
        return self.get_items_list(start, count, 'title = ""')

    def update_item_by_url(self, url: str, body_params: Dict[str, Any]) -> bool:
        item = self.get_item_by_url(url)
        if not item:
            return False
        item_id = item.id
        self.conn.execute(
            text(f"update items set {body_params} where id = '{item_id}'")
        ).fetchall()
        return True

    def update_item_deleted(self, url: str) -> bool:
        return self.update_item_by_url(url, {"deleted": True})

    def create_item(self, url: str, img_path: str) -> Sequence[Row]:
        return self.conn.execute(
            text(f"insert into items (url, img_path) values ('{url}', '{img_path}')")
        ).fetchall()
