from typing import Optional, Iterator, Dict, Union, get_origin, get_args

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo
from pocketbase import PocketBase
from pocketbase.services.record_service import RecordService
from pocketbase.services.collection_service import CollectionService
from pocketbase.models.collection import Collection
from pocketbase.errors import ClientResponseError

from marketface.logger import getLogger


logger = getLogger("marketface.data.items")


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


class BaseRepo:

    type_map = {
        str: "text",
        float: "number",
        int: "number",
        bool: "bool",
    }

    def setup(self, client: PocketBase, collection_name: str) -> None:
        self.client: PocketBase = client
        self.collection_name: str = collection_name
        self.collection: RecordService = self.client.collection(self.collection_name)

    def _validate(self, data) -> Optional[Item]:
        if not data:
            return None
        return Item.model_validate(data)

    def first(self, query: str) -> Optional[Item]:
        record = self.collection.get_first_list_item(query)
        return self._validate(record)

    def list(self, start: int, count: int, params: Optional[Dict] = None) -> Iterator[Optional[Item]]:
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

    def update(self, item: Item) -> Optional[Item]:
        record = self.collection.update(item.id, item.model_dump())
        return self._validate(record)

    def create(self, data: Dict) -> Optional[Item]:
        item = self._validate(data)
        if not item:
            return None
        self.collection.create(item.model_dump())

    def table_exists(self) -> Optional[Collection]:
        try:
            return self.client.collections.get_one(self.collection_name)
        except ClientResponseError as e:
            if e.status != 404:
                raise e

    def get_pb_type(self, field_name: str, field_info: FieldInfo) -> str:

        if field_name == 'url':
            pb_type = 'url'
        else:
            annotation = field_info.annotation
            origin = get_origin(annotation)

            if origin is Union:
                inner_type = next((t for t in get_args(annotation) if t is not type(None)), None)
            else:
                inner_type = annotation

            pb_type = BaseRepo.type_map.get(inner_type, "json")

        return pb_type



class ItemRepo(BaseRepo):

    def __init__(self, client: PocketBase) -> None:
        self.setup(client, "items")

    def get_by_url(self, url: str) -> Optional[Item]:
        return self.first(f'url = "{url}"')

    def get_incomplete(self) -> Iterator[Optional[Item]]:
        yield from self.all({"filter": "title = ''"})

    def set_deleted(self, item: Item) -> Optional[Item]:
        item.deleted = True
        return self.update(item)

    def create_table(self) -> Optional[Collection]:

        if self.table_exists():
            logger.info(
                "Collection '%s' already exists. Skipping creation.",
                self.collection_name,
            )
            return
        else:
            logger.info(
                "Collection '%s' not found. Attempting to create...",
                self.collection_name,
            )

        collection_schema = []

        # TODO iterate over each field in Item model
        for field_name, field_info in Item.model_fields.items():
            # Exclude fields from the base model (id, created, updated) as
            # PocketBase manages them automatically.
            if field_name in PocketBaseModel.model_fields:
                continue

            pb_type = self.get_pb_type(field_name, field_info)

            collection_schema.append({
                "name": field_info.alias or field_name,
                "type": pb_type,
                "required": field_info.is_required(),
                "unique": False, # TODO
                "options": {} # TODO
            })

        collection_data = {
            "name": self.collection_name,
            "type": "base",
            "schema": collection_schema,
        }

        collections: CollectionService = self.client.collections
        return collections.create(collection_data)