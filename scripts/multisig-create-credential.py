# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from time import sleep

import requests
from keri import kering
from keri.app import signing
from keri.app.keeping import Algos
from keri.core import coring, eventing, serdering
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient

TIME = "2023-09-25T16:01:37.000000+00:00"


def create_credential():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier)
    print(client.controller)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    evt, siger = client.ctrl.event()
    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))

    client.connect(url=url)
    assert client.agent is not None
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
    # assert client.ctrl.ridx == 0

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    oobis = client.oobis()
    identifiers = client.identifiers()
    registries = client.registries()
    credentials = client.credentials()
    exchanges = client.exchanges()
    operations = client.operations()
    ipex = client.ipex()

    (_, _, op) = identifiers.create("multisig3", bran="0123456789lmnopqrstuv")
    icp = op["response"]
    serder = serdering.SerderKERI(sad=icp)
    assert serder.pre == "EOGvmhJDBbJP4zeXaRun5vSz0O3_1zB10DwNMyjXlJEv"
    print(f"created AID {serder.pre}")

    identifiers.addEndRole("multisig3", eid=client.agent.pre)

    print(f"OOBI for {serder.pre}:")
    oobi = oobis.get("multisig3")
    print(oobi)

    op = oobis.resolve(oobi="http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness",
                       alias="multisig1")

    print("resolving oobi for multisig1")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    multisig1 = op["response"]
    print("resolving oobi for multisig2")
    op = oobis.resolve(oobi="http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness",
                       alias="multisig2")
    print("... done")

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    multisig2 = op["response"]

    m3 = identifiers.get("multisig3")
    agent0 = m3["state"]
    print(f"agent is {agent0}")

    states = rstates = [multisig2, multisig1, agent0]

    icp, isigs, op = identifiers.create("multisig", algo=Algos.group, mhab=m3,
                                        isith=["1/3", "1/3", "1/3"], nsith=["1/3", "1/3", "1/3"],
                                        toad=3,
                                        wits=[
                                            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
                                        ],
                                        states=states,
                                        rstates=rstates)

    smids = [state['i'] for state in states]
    recp = [state['i'] for state in [multisig2, multisig1]]

    embeds = dict(
        icp=eventing.messagize(serder=icp, sigers=[coring.Siger(qb64=sig) for sig in isigs])
    )

    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/icp",
                   payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                   embeds=embeds, recipients=recp)

    print("waiting on multisig creation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    gAid = op["response"]
    print(f"group multisig created {gAid}")

    op = oobis.resolve(oobi="http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                       alias="vc")

    print("resolving oobi for credential schema")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    m = identifiers.get("multisig")

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
    acdc = signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said))
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
    create_credential()
