from pocketbase import PocketBase

client = PocketBase('http://127.0.0.1:8090')

# this is not a real password
admin_data = client.admins.auth_with_password("romayengineer@gmail.com", "adminadmin!")

assert admin_data.is_valid, "invalid database credentials"

def get_first_item(query_filter):
    return client.collection("items").get_first_list_item(query_filter)

def get_item_by_url(url):
    return get_first_item(f'url = "{url}"')

def create_item(url, img_path):
    client.collection("items").create({
        "url": url,
        "img_path": img_path,
    })