import sys
from typing import Dict

from pocketbase import PocketBase
from pocketbase.utils import ClientResponseError

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


assert admin_data and admin_data.is_valid, "invalid database credentials"


def get_first_item(query_filter):
    return client.collection("items").get_first_list_item(query_filter)


def get_item_by_url(url):
    return get_first_item(f'url = "{url}"')

def get_all(filter=None):
    page = 1
    items = []
    while True:
        new_items = get_items_list(page, 100).items
        if not new_items:
            break
        items.extend(new_items)
        page += 1
    return items

def get_items_list(start, count, filter=None):
    params = {}
    if filter:
        params["filter"] = filter
    return client.collection("items").get_list(start, count, params)


def get_items_incomplete(start, count):
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
    client.collection("items").update(rid, body_params)
    return True


def update_item_deleted(url: str) -> bool:
    body_params = {"deleted": True}
    print("marked as deleted! ", url)
    return update_item_by_url(url, body_params)


def create_item(href_full, img_path):
    client.collection("items").create(
        {
            "url": href_full,
            "img_path": img_path,
        }
    )
