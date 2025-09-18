# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from dataclasses import asdict

import requests
from keri import kering
from keri.core import serdering, signing
from keri.core.coring import Tiers

from signify.core import api


def create_agent_with_manual_icp_evt():
    """
    With an inception event pasted in through the console, create an agent manually,
    not using SignifyClient
    """
    url = "http://localhost:3901"
    boot_url = "http://localhost:3903"
    tier = Tiers.low
    stem = "signify:controller"

    ims = input("Type of paste controller inception event:")
    icp_evt = serdering.SerderKERI(raw=ims.encode("utf-8"))
    siger = signing.Siger(qb64=ims[icp_evt.size:])

    agent_boot = api.AgentBoot(
        icp=icp_evt.ked,
        sig=siger.qb64,
        stem=stem,
        pidx=1,
        tier=tier
    )
    res = requests.post(url=f"{boot_url}/boot", json=asdict(agent_boot))

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    print("Person agent created")
    print(res.text)


if __name__ == "__main__":
    create_agent_with_manual_icp_evt()
