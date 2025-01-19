# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.signifying

"""

from dataclasses import dataclass


@dataclass
class SignifyState:
    """
    Initialization state for a SignifyClient instance
    """
    controller: dict = None
    agent : dict = None
    ridx: int = None
    pidx: int = None