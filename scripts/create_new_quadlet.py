# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from time import sleep

import requests
from keri import kering
from keri.core import coring
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient

URL = "http://localhost:3901"


def create_quadlet():
    bran1 = "0123456789abcdefghsec"
    bran2 = "0123456789abcdefghsaw"
    bran3 = "0123456789abcdefghsg4"
    bran4 = "0123456789abcdefgh0z5"

    client1 = create_agent(bran1,
                           "EIX9c9DUvzXK5E7EnBybtIizdo9KBQISOrYb0JNQ7OFI",
                           "EHkbqFLxa5TrSjAiZsC5gtHmynGYkUhgOyNWDRKbfSPd")

    client2 = create_agent(bran2,
                           "EKzJM2IBFSkAIz-RpXUv7GhvTdPPvpNl9nf8emPUcXqi",
                           "EAiO7QUJcyDXJ5WfToUJqJV437N5p9NXbpMXb9XEjUti")

    client3 = create_agent(bran3,
                           "ECyAJ3zRVKO5vr8LbssPnNEKf10MmgF9BGqB06lvFVR0",
                           "EMY8KpPNknneXlrhGIFnN7UUOMO27g-M5SO5MRqXPzwe")

    client4 = create_agent(bran4,
                           "ENL1pd5iTRBe6XMMD-yi05W6_bVz1nQFvxWM52I6DTRk",
                           "EHLxs9z_5xwLuRBuS-xkQwIJvZMJ6d9dhxSo9fYn8lCs")

    create_aid(client1, "multisig1", bran1, "EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc")
    create_aid(client2, "multisig2", bran2, "EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5")
    create_aid(client3, "multisig3", bran3, "EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh")
    create_aid(client4, "multisig4", bran4, "EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs")

    oobi(client2, "multisig1", "http://127.0.0.1:3902/oobi/EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc")
    oobi(client3, "multisig1", "http://127.0.0.1:3902/oobi/EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc")
    oobi(client4, "multisig1", "http://127.0.0.1:3902/oobi/EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc")

    oobi(client1, "multisig2", "http://127.0.0.1:3902/oobi/EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5")
    oobi(client3, "multisig2", "http://127.0.0.1:3902/oobi/EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5")
    oobi(client4, "multisig2", "http://127.0.0.1:3902/oobi/EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5")

    oobi(client1, "multisig3", "http://127.0.0.1:3902/oobi/EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh")
    oobi(client2, "multisig3", "http://127.0.0.1:3902/oobi/EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh")
    oobi(client4, "multisig3", "http://127.0.0.1:3902/oobi/EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh")

    oobi(client1, "multisig4", "http://127.0.0.1:3902/oobi/EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs")
    oobi(client2, "multisig4", "http://127.0.0.1:3902/oobi/EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs")
    oobi(client3, "multisig4", "http://127.0.0.1:3902/oobi/EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs")

    oobi(client1, "old-multisig1", "http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client1, "old-multisig2", "http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client1, "old-multisig3", "http://127.0.0.1:5642/oobi/EMkvHBDM2n9rvjnUiLvdAFJjNZ81Fp0QmEgto-2cG8CS/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client1, "old-multisig4", "http://127.0.0.1:5642/oobi/EAV9iv9aFLy2AULDisAfeHgLy1-NmKP6fEVddYAE7dyf/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")

    oobi(client2, "old-multisig1", "http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client2, "old-multisig2", "http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client2, "old-multisig3", "http://127.0.0.1:5642/oobi/EMkvHBDM2n9rvjnUiLvdAFJjNZ81Fp0QmEgto-2cG8CS/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client2, "old-multisig4", "http://127.0.0.1:5642/oobi/EAV9iv9aFLy2AULDisAfeHgLy1-NmKP6fEVddYAE7dyf/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")

    oobi(client3, "old-multisig1", "http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client3, "old-multisig2", "http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client3, "old-multisig3", "http://127.0.0.1:5642/oobi/EMkvHBDM2n9rvjnUiLvdAFJjNZ81Fp0QmEgto-2cG8CS/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client3, "old-multisig4", "http://127.0.0.1:5642/oobi/EAV9iv9aFLy2AULDisAfeHgLy1-NmKP6fEVddYAE7dyf/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")

    oobi(client4, "old-multisig1", "http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client4, "old-multisig2", "http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client4, "old-multisig3", "http://127.0.0.1:5642/oobi/EMkvHBDM2n9rvjnUiLvdAFJjNZ81Fp0QmEgto-2cG8CS/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")
    oobi(client4, "old-multisig4", "http://127.0.0.1:5642/oobi/EAV9iv9aFLy2AULDisAfeHgLy1-NmKP6fEVddYAE7dyf/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")

    oobi(client1, "multisig", "http://127.0.0.1:5642/oobi/EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I/witness")
    oobi(client2, "multisig", "http://127.0.0.1:5642/oobi/EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I/witness")
    oobi(client3, "multisig", "http://127.0.0.1:5642/oobi/EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I/witness")
    oobi(client4, "multisig", "http://127.0.0.1:5642/oobi/EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I/witness")


def create_agent(bran, ctrlAid, agentAid):
    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == ctrlAid

    evt, siger = client.ctrl.event()

    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    client.connect(url=URL, )
    assert client.agent is not None

    assert client.agent.pre == agentAid
    assert client.agent.delpre == ctrlAid
    print(f"Agent {client.agent.pre} created for controller {client.controller}")

    return client


def create_aid(client, name, bran, pre):
    identifiers = client.identifiers()
    operations = client.operations()

    wits = [
        "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
        "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
    ]

    op = identifiers.create(name, bran=bran, wits=wits, toad="2")
    op = op[2]

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp = coring.Serder(ked=op["response"])
    print(icp.pre)
    assert icp.pre == pre

    identifiers.addEndRole(name, eid=client.agent.pre)

    print(f"Created AID {name}: {icp.pre}")


def oobi(client, alias, url):
    oobis = client.oobis()
    operations = client.operations()

    print(f"Resolving oobi to {alias}")
    op = oobis.resolve(
        oobi=url,
        alias=alias)
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")


if __name__ == "__main__":
    create_quadlet()
