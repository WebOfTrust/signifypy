# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from time import sleep

from keri.core import coring
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def create_aid():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()

    aids = identifiers.list()
    assert aids == []

    wits = [
        "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
        "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
    ]

    op = identifiers.create("aid1", bran="0123456789abcdefghijk", wits=wits, toad="2")

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp = coring.Serder(ked=op["response"])
    assert icp.pre == "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"
    print(f"Person AID {icp.pre} created")

    identifiers.addEndRole("aid1", eid=client.agent.pre)

    print("person resolving external...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:5642/oobi/EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW/witness/BBilc4"
             "-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        alias="external")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("person resolving qvi...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:5642/oobi/EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX/witness/BBilc4"
             "-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        alias="qvi")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("person resolving legal-entity...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:5642/oobi/EIitNxxiNFXC1HDcPygyfyv3KUlBfS_Zf-ZYOvwjpTuz/witness/BBilc4"
             "-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        alias="legal-entity")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("resolving schema EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    op = oobis.resolve(
        oobi="http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("resolving schema ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY")
    op = oobis.resolve(
        oobi="http://127.0.0.1:7723/oobi/ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("resolving schema EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g")
    op = oobis.resolve(
        oobi="http://127.0.0.1:7723/oobi/EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("resolving schema EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw")
    op = oobis.resolve(
        oobi="http://127.0.0.1:7723/oobi/EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")


if __name__ == "__main__":
    create_aid()
