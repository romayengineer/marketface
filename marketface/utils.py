def get_file_name_from_url(href: str) -> str:
    return href[1:].replace("/", "_")


def shorten_item_url(url):
    """
    Takes the full url of a marketplace item and shortens it
    to the following format
    /marketplace/item/<number>
    """
    # the url must start with the following
    start = "/marketplace/item/"
    if not url.startswith(start):
        return url
    # start checking from the end of the starting string
    # (the one above)
    i = len(start)
    # get the length of the url
    u = len(url)
    # if the url is not longer than the starting string
    # return the original url
    if not u > i:
        return url
    # loop through each character of the url
    while i < u:
        # if the character is not a digit break the loop
        if not url[i].isdigit():
            break
        # move to the next character
        i += 1
    # the shortened url is all the characters from the beginning
    # of the string up to the last non digit character
    shortened = url[:i]
    # the last character of the shortened url must be a digit
    # if not shortened[-1].isdigit():
    #     raise Exception("marketplace item url does not have an id")
    # return the shortened url
    return shortened
