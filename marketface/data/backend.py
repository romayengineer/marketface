import sys
from pocketbase import PocketBase
from pocketbase.utils import ClientResponseError


def auth() -> PocketBase:
    # TODO use a config file for this
    client = PocketBase("http://127.0.0.1:8090")

    admin_data = None

    try:
        # this is not a real password
        admin_data = client.admins.auth_with_password(
            email="romayengineer@gmail.com",
            password="adminadmin!",
        )
    except ClientResponseError as e:
        print(e)
        print("did you run pocketbase serve? from data/base")
        sys.exit(1)

    assert admin_data and admin_data.is_valid, "invalid database credentials"

    return client