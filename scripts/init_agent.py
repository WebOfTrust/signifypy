# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

import pytest
import requests
from keri import kering
from keri.core import coring
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def create_agent():
    url = "http://localhost:3901"
    tier = Tiers.med
    stem = "signify:controller"

    ims = input("Type of paste controller inception event:")
    serder = serdering.SerderKERIraw=ims.encode("utf-8"))
    siger = coring.Siger(qb64=ims[serder.size:])

    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=serder.ked,
                            sig=siger.qb64,
                            stem=stem,
                            pidx=1,
                            tier=tier))

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    print("Person agent created")
    print(res.text)


if __name__ == "__main__":
    create_agent()
