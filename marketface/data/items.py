import json
from datetime import datetime
from typing import Type, Optional, Iterator, Dict, Union, get_origin, get_args

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo
from pocketbase import PocketBase
from pocketbase.services.record_service import RecordService
from pocketbase.services.collection_service import CollectionService
from pocketbase.models.utils.base_model import BaseModel as PocketBaseBaseModel
from pocketbase.utils import ClientResponseError

from marketface.logger import getLogger


logger = getLogger("marketface.data.items")


class PocketBaseModel(BaseModel):
    """
    Pocketbase handles this on its own
    """

    id: Optional[str] = Field(None)
    created: Optional[datetime] = Field(None)
    updated: Optional[datetime] = Field(None)


class Item(PocketBaseModel):
    url: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    priceStr: Optional[str] = Field(None)
    priceUsd: Optional[float] = Field(0.0)
    priceArs: Optional[float] = Field(0.0)
    usdArsRate: float = Field(1230.00)
    img_path: Optional[str] = Field(None)
    usd: Optional[bool] = Field(False)
    deleted: Optional[bool] = Field(False)
    reviewed: Optional[bool] = Field(False)
    new: Optional[bool] = Field(False)

    class Config:
        from_attributes = True

    def log(self):
        for field_name in Item.model_fields:
            logger.info("%s: %s", field_name, getattr(self, field_name))



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

    def _validate(self, data) -> Item:
        return Item.model_validate(data)

    def first(self, query: str) -> Item:
        record = self.collection.get_first_list_item(query)
        return self._validate(record)

    def list(self, start: int, count: int, params: Optional[Dict] = None) -> Iterator[Item]:
        records = self.collection.get_list(start, count, params or {}).items
        for record in records:
            yield self._validate(record)

    def all(self, params: Optional[Dict] = None) -> Iterator[Item]:
        page = 1
        while True:
            items = self.list(page, 100, params)
            if not items:
                break
            for item in items:
                yield self._validate(item)
            page += 1

    def update(self, item: Item) -> Item:
        if not item.id:
            raise ValueError("id is required")
        record = self.collection.update(
            item.id,
            item.model_dump(
                exclude={"id", "created", "updated"},
            ),
        )
        return self._validate(record)

    def create(self, data) -> Item:
        item = self._validate(data)
        response = self.collection.create(item.model_dump())
        return self._validate(response)

    def table_exists(self) -> Optional[PocketBaseBaseModel]:
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

    def _create_table(self, table: Type[PocketBaseModel]) -> Optional[PocketBaseBaseModel]:

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
        for field_name, field_info in table.model_fields.items():
            # Exclude fields from the base model (id, created, updated) as
            # PocketBase manages them automatically.
            if field_name in PocketBaseModel.model_fields:
                continue

            pb_type = self.get_pb_type(field_name, field_info)

            options = {}
            if pb_type == 'text':
                # Example: Set a max length for text fields
                options['max'] = 3000

            collection_schema.append({
                "name": field_info.alias or field_name,
                "type": pb_type,
                "required": field_info.is_required(),
                "system": False,
                "presentable": True,
                "unique": False, # TODO
                "options": options # TODO
            })

        collection_data = {
            "name": self.collection_name,
            "type": "base",
            "schema": collection_schema,
        }

        # logger.info("collection_data:\n %s", json.dumps(collection_data, indent=4))

        collections: CollectionService = self.client.collections
        return collections.create(body_params=collection_data)


class ItemRepo(BaseRepo):

    def __init__(self, client: PocketBase) -> None:
        self.setup(client, "items")

    def get_by_url(self, url: str) -> Item:
        return self.first(f'url = "{url}"')

    def get_incomplete(self) -> Iterator[Item]:
        yield from self.all({"filter": "title = '' && deleted = false"})

    def set_deleted(self, item: Item) -> Item:
        item.deleted = True
        logger.warning("setting item to deleted %s", item.url)
        return self.update(item)

    def create_table(self) -> Optional[PocketBaseBaseModel]:
        return self._create_table(Item)