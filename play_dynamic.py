"""
this is for quick development cycle as I reload this module
dynamically and I update the code to see the changing without
reloading the script or browser
"""

def search(page):
    page.goto("https://www.facebook.com/marketplace/buenosaires/search?minPrice=140000&query=macbook&exact=false")

def test(page):
    search(page)