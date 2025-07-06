import sys
from typing import Dict, List

from pocketbase import PocketBase
from pocketbase.utils import ClientResponseError
from pocketbase.models.utils.list_result import ListResult
from pocketbase.models.utils.base_model import BaseModel

# TODO use a config file for this
client = PocketBase("http://127.0.0.1:8090")

admin_data = None

try:
    # this is not a real password
    admin_data = client.admins.auth_with_password(
        "romayengineer@gmail.com", "adminadmin!"
    )
except ClientResponseError as e:
    print(e)
    print("did you run pocketbase serve? from data/base")
    sys.exit(1)

TABLE_NAME = "items"

assert admin_data and admin_data.is_valid, "invalid database credentials"


def create_table(collection_name: str):

    collection_schema = [
        {"name": "url", "type": "url", "required": False, "unique": False, "options": {}},
        {"name": "title", "type": "text", "required": False, "unique": False, "options": {"max": 1000}},
        {"name": "description", "type": "text", "required": False, "unique": False, "options": {"max": 3000}},
        {"name": "img_path", "type": "text", "required": False, "unique": False, "options": {}},
        {"name": "priceUsd", "type": "number", "required": False, "unique": False, "options": {}},
        {"name": "priceArs", "type": "number", "required": False, "unique": False, "options": {}},
        {"name": "usdArsRate", "type": "number", "required": False, "unique": False, "options": {}},
        {"name": "usd", "type": "bool", "required": False, "unique": False, "options": {}},
        {"name": "deleted", "type": "bool", "required": False, "unique": False, "options": {}},
        {"name": "reviewed", "type": "bool", "required": False, "unique": False, "options": {}},
        {"name": "new", "type": "bool", "required": False, "unique": False, "options": {}},
    ]

    # Data payload for creating the collection
    collection_data = {
        "name": collection_name,
        "type": "base",
        "schema": collection_schema,
    }

    try:
        print(f"\nAttempting to create collection '{collection_name}'...")

        created_collection = client.collections.create(collection_data)

        print(f"Successfully created collection: {created_collection.name} (ID: {created_collection.id})")

    except Exception as e:
        print(f"An unexpected error occurred during collection creation: {e}")


def get_first_item(query_filter) -> BaseModel:
    return client.collection(TABLE_NAME).get_first_list_item(query_filter)


def get_item_by_url(url) -> BaseModel:
    return get_first_item(f'url = "{url}"')

def get_all() -> List[BaseModel]:
    page = 1
    items = []
    while True:
        new_items = get_items_list(page, 100).items
        if not new_items:
            break
        items.extend(new_items)
        page += 1
    return items

def get_items_list(start, count, filter=None) -> ListResult:
    params = {}
    if filter:
        params["filter"] = filter
    return client.collection(TABLE_NAME).get_list(start, count, params)


def get_items_incomplete(start, count) -> ListResult:
    """
    returns the list of items missing
    title description price and other details
    """
    return get_items_list(start, count, 'title = ""')


def update_item_by_url(url: str, body_params: Dict) -> bool:
    record = get_item_by_url(url)
    if not record:
        return False
    rid = record.id
    client.collection(TABLE_NAME).update(rid, body_params)
    return True

def update_item_by_id(rid: str, body_params: Dict) -> bool:
    client.collection(TABLE_NAME).update(rid, body_params)
    return True


def update_item_deleted(url: str) -> bool:
    body_params = {"deleted": True}
    print("marked as deleted! ", url)
    return update_item_by_url(url, body_params)


def create_item(href_full, img_path=""):
    client.collection(TABLE_NAME).create(
        {
            "url": href_full,
            "img_path": img_path,
        }
    )
