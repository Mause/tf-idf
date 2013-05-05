import re

TOKEN_RE = re.compile(r"[\w'`]+", flags=re.UNICODE)


def tokenize(string):
    string = string.lower()
    string = TOKEN_RE.findall(string)
    return string, len(string)
