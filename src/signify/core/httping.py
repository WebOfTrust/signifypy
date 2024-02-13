# -*- encoding: utf-8 -*-
"""
SignifyPy
signify.core.httping module

"""
from typing import Tuple


def parseRangeHeader(header: str, typ: str) -> Tuple[int, int, int]:
    """ Parse start, end and total from HTTP Content-Range header value

    Parameters:
        header (str): HTTP Content-Range header value
        typ (str): Type in range header

    Returns: Tuple[int, int int]

    """
    data = header.lstrip(f"{typ} ")

    values = data.split("/")
    rng = values[0].split("-")

    return int(rng[0]), int(rng[1]), int(values[1])