"""
this is for quick development cycle as I reload this module
dynamically and I update the code to see the changing without
reloading the script or browser
"""


shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page)",
    "c": "play_dynamic.collect_articles(page)",
    "h": "help()",
    "exit": "sys.exit(0)",
}

def collect_articles(page):
    print("collect articles")

def login(page):
    page.goto("https://www.facebook.com")

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    login(page)