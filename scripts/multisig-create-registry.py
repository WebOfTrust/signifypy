# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from time import sleep

from keri.app import signing
from keri.core import eventing, coring
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient

TIME = "2023-09-25T16:01:37.000000+00:00"

def create_registry():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()
    registries = client.registries()
    credentials = client.credentials()
    exchanges = client.exchanges()
    operations = client.operations()
    ipex = client.ipex()

    m = identifiers.get("multisig")
    m3 = identifiers.get("multisig3")

    vcp, anc, rsigs, op = registries.create(hab=m, registryName="vLEI",
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

    print("registry created")

    registry = registries.get(name="multisig", registryName="vLEI")

    m = identifiers.get("multisig")
    data = {
        "LEI": "5493001KJTIIGC8Y1R17"
    }
    creder, iserder, anc, sigs, op = credentials.create(m, registry, data=data,
                                                        schema="EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                                                        recipient="ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k",
                                                        timestamp=TIME)

    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, iserder.saider)
    iss = registries.serialize(iserder, anc)

    embeds = dict(
        acdc=acdc,
        iss=iss,
        anc=eventing.messagize(serder=anc, sigers=[coring.Siger(qb64=sig) for sig in sigs])
    )
    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/iss",
                   payload=dict(gid=m["prefix"]),
                   embeds=embeds, recipients=recp)

    print("waiting on credential creation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    m = identifiers.get("multisig")
    grant, sigs, end = ipex.grant(m, recp="ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k", acdc=acdc,
                                  iss=iss, message="",
                                  anc=eventing.messagize(serder=anc, sigers=[coring.Siger(qb64=sig) for sig in sigs]),
                                  dt=TIME)

    mstate = m["state"]
    seal = eventing.SealEvent(i=m["prefix"], s=mstate["ee"]["s"], d=mstate["ee"]["d"])
    ims = eventing.messagize(serder=grant, sigers=[coring.Siger(qb64=sig) for sig in sigs], seal=seal)
    ims.extend(end)
    embeds = dict(
        exn=ims
    )

    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/exn",
                   payload=dict(gid=m["prefix"]),
                   embeds=embeds, recipients=recp)


if __name__ == "__main__":
    create_registry()
