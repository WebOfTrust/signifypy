# -*- encoding: utf-8 -*-
from typing import Tuple
"""
SignifyPy
signify.core.httping module

"""


def parseRangeHeader(header: str) -> Tuple[int, int, int]:
    """ Parse start, end and total from HTTP Content-Range header value

    Parameters:
        header (str): HTTP Content-Range header value

    Returns: Tuple[int, int int]

    """
    data = header.lstrip("aids ")

    values = data.split("/")
    rng = values[0].split("-")

    return int(rng[0]), int(rng[1]), int(values[1])