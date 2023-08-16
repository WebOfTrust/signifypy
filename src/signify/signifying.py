# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.signifying

"""

from dataclasses import dataclass


@dataclass
class State:
    controller: dict = None
    agent : dict = None
    ridx: int = None
    pidx: int = None