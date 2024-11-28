lowercase = [chr(n) for n in range(ord("a"), ord("a") + 26)] + ["ñ"]  # Spanish letter
uppercase = [chr(n) for n in range(ord("A"), ord("A") + 26)] + ["Ñ"]
letters = lowercase + uppercase
numbers = [str(n) for n in range(10)]
especial = [
    " ",
    "’",
    "'",
    '"',
    ".",
    ",",
    ";",
    "!",
    "?",
    "_",
    "-",
    "/",
    "\\",
    "|",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
]
alphabet = letters + numbers + especial


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
    if u <= i:
        return url
    # loop through each character of the url
    while i < u and url[i].isdigit():
        # if the character is not a digit break the loop
        # move to the next character
        i += 1
    # the shortened url is all the characters from the beginning
    # of the string up to the last non digit character
    # shortened = url[:i]
    # the last character of the shortened url must be a digit
    # if not shortened[-1].isdigit():
    #     raise Exception("marketplace item url does not have an id")
    # return the shortened url
    return url[:i]


def oneline(text):
    """
    puts everything in one line and removes unwanted characters
    like for example emojis
    """
    text = text.replace("\n", " ")
    newText = ""
    i = 0
    while i < len(text):
        c = text[i]
        if c == " ":
            newText += " "
            i += 1
            while i < len(text):
                c = text[i]
                if c == " ":
                    i += 1
                else:
                    break
            continue
        if c not in alphabet:
            i += 1
            continue
        newText += c
        i += 1
    return newText.strip()


def firstnumbers(numberStr):
    i = 0
    newNumber = ""
    while i < len(numberStr):
        c = numberStr[i]
        if c not in numbers:
            break
        newNumber += c
        i += 1
    return newNumber
