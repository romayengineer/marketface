from typing import Optional, Iterator, Dict

from pocketbase import PocketBase
from pydantic import BaseModel, Field


class PocketBaseModel(BaseModel):
    id: str
    created: str
    updated: str


class Item(PocketBaseModel):
    url: str
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    img_path: Optional[str] = Field(None)
    price_usd: Optional[float] = Field(None)
    price_ars: Optional[float] = Field(None)
    usd_ars_rate: Optional[float] = Field(None)
    usd: Optional[bool] = Field(False)
    deleted: Optional[bool] = Field(False)
    reviewed: Optional[bool] = Field(False)
    new: Optional[bool] = Field(False)

    class Config:
        from_attributes = True


class ItemRepo:

    def __init__(self, client: PocketBase):
        self.client = client
        self.collection = self.client.collection("items")

    def _validate(self, data) -> Optional[Item]:
        if not data:
            return None
        return Item.model_validate(data)

    def first(self, query: str) -> Optional[Item]:
        record = self.collection.get_first_list_item(query)
        return self._validate(record)

    def by_url(self, url: str) -> Optional[Item]:
        return self.first(f'url = "{url}"')

    def list(self, start: int, count: int, params: Optional[Dict] = None) -> Iterator[Optional[Item]]:
        params = params or {}
        records = self.collection.get_list(start, count, params).items
        for record in records:
            yield self._validate(record)

    def all(self, params: Optional[Dict] = None) -> Iterator[Optional[Item]]:
        page = 1
        while True:
            items = self.list(page, 100, params)
            if not items:
                break
            for item in items:
                yield self._validate(item)
            page += 1

    def incomplete(self) -> Iterator[Optional[Item]]:
        yield from self.all({"filter": "title = ''"})

    def update(self, item: Item) -> Optional[Item]:
        record = self.collection.update(item.id, item.model_dump())
        return self._validate(record)

    def mark_deleted(self, item: Item) -> Optional[Item]:
        item.deleted = True
        return self.update(item)

    def create(self, data: Dict) -> Optional[Item]:
        item = self._validate(data)
        if not item:
            return None
        self.collection.create(item.model_dump())