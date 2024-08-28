"""
this is for quick development cycle as I reload this module
dynamically and I update the code to see the changing without
reloading the script or browser

once the functions in here are well developed and tested
I'll move them to the main script
"""


shortcuts = {
    # shortcut for search
    "s": "play_dynamic.search(page)",
    # shortcut for quick testing a new function
    "t": "play_dynamic.test(page)",
    "l": "play_dynamic.login(page)",
    "c": "play_dynamic.collect_articles(page)",
    "h": "play_dynamic.help()",
    "exit": "sys.exit(0)",
}

def help():
    print("Getting started tutorial:")
    print("")
    print("1. run `l` this will load facebook's login page")
    print("   login as usual with your user and password")
    print("2. run `s` to open the marketplace and search")
    print("   by default it searchs for a macbook")
    print("3. run `c` to collect the marketplace items")
    print("   from the marketplace search page")
    print("")
    for shortcut, command in shortcuts.items():
        print(shortcut, " --> ", command)

def collect_articles(page):
    print("collect articles")

def login(page):
    page.goto("https://www.facebook.com")

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    login(page)