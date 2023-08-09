# -*- encoding: utf-8 -*-
"""
SignifyPy
signify.core.httping module

"""


def parseRangeHeader(header: str):
    """ Parse start, end and total from HTTP Content-Range header value

    Parameters:
        header (str): HTTP Content-Range header value

    Returns:

    """
    data = header.lstrip("aids ")

    values = data.split("/")
    rng = values[0].split("-")

    return int(rng[0]), int(rng[1]), int(values[1])