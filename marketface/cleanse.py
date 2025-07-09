

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
    "$",
]
alphabet = letters + numbers + especial


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