import re

TOKEN_RE = re.compile(r"[\w'`]+", flags=re.UNICODE)


def tokenize(string):
    "converts string to lowercase, and uses re to split appart the words"
    string = string.lower()
    string = TOKEN_RE.findall(string)
    return string
