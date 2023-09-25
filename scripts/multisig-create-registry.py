# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from time import sleep

from keri.core import eventing, coring
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def create_registry():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()
    registries = client.registries()
    exchanges = client.exchanges()
    operations = client.operations()

    m = identifiers.get("multisig")
    m3 = identifiers.get("multisig3")

    vcp, anc, rsigs, op = registries.create(name="multisig", registryName="vLEI",
                                            nonce="AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s")

    embeds = dict(
        vcp=vcp.raw,
        anc=eventing.messagize(serder=anc, sigers=[coring.Siger(qb64=sig) for sig in rsigs])
    )

    recp = ["EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4", "EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1"]
    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/vcp",
                   payload=dict(gid=m["prefix"], usage="Issue vLEIs"),
                   embeds=embeds, recipients=recp)

    print("waiting on credential registry creation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    print(op["response"])


if __name__ == "__main__":
    create_registry()
