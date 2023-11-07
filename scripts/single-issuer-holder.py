# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from time import sleep

import requests
import datetime
import pysodium
from keri import kering
from keri.app import signing
from keri.app.keeping import Algos
from keri.core import coring, eventing
from keri.core.coring import Tiers
from keri.help import helping
from signify.app.clienting import SignifyClient

URL = 'http://127.0.0.1:3901'
BOOT_URL = 'http://127.0.0.1:3903'
SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
WITNESS_AIDS = ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha']
SCHEMA_OOBI = 'http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'

def random_passcode():
    return coring.Salter(raw=pysodium.randombytes(pysodium.crypto_sign_SEEDBYTES)).qb64

def create_timestamp():
    return helping.nowIso8601()

def connect():
    client = SignifyClient(passcode=random_passcode(), tier=Tiers.low)

    evt, siger = client.ctrl.event()
    res = requests.post(url=BOOT_URL + "/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))

    client.connect(url=URL)

    return client

def create_identifier(client: SignifyClient, name: str):
    result = client.identifiers().create(name, toad=str(len(WITNESS_AIDS)), wits=WITNESS_AIDS)
    op = result[2]

    while not op["done"]:
        op = client.operations().get(op["name"])
        sleep(1)

    hab = client.identifiers().get(name)

    client.identifiers().addEndRole(name=name, eid=client.agent.pre)

    return hab["prefix"]

def get_agent_oobi(client: SignifyClient, name: str):
    result = client.oobis().get(name, role='agent')
    return result["oobis"][0]


def resolve_oobi(client: SignifyClient, oobi: str, alias: str):
    op = client.oobis().resolve(oobi, alias)
    while not op['done']:
        op = client.operations().get(op["name"])
        sleep(1)

def create_registry(client: SignifyClient, name: str, registry_name: str):
    hab = client.identifiers().get(name)
    result = client.registries().create(hab=hab, registryName=registry_name)
    op = result[3]
    while not op['done']:
        op = client.operations().get(op["name"])
        sleep(1)

    registry = client.registries().get(name=name, registryName=registry_name)
    return registry

def issue_credential(client: SignifyClient, name:str, registry_name: str, schema: str, recipient: str, data):
    hab = client.identifiers().get(name)
    registry = client.registries().get(name, registryName=registry_name)
    creder, iserder, anc, sigs, op = client.credentials().create(hab, registry=registry, data=data, schema=schema, recipient=recipient, timestamp=create_timestamp())

    while not op['done']:
        print(f"Waiting for creds... {op['name']}")
        op = client.operations().get(op['name'])
        sleep(1)

    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, iserder.saider)
    iss = client.registries().serialize(iserder, anc)

    grant, sigs, end = client.ipex().grant(hab, recp=recipient, acdc=acdc,
                                  iss=iss, message="",
                                  anc=eventing.messagize(serder=anc, sigers=[coring.Siger(qb64=sig) for sig in sigs]),
                                  dt=create_timestamp())

    client.exchanges().sendFromEvents(name=name, topic="credential", exn=grant, sigs=sigs, atc=end, recipients=[recipient])

    return

def wait_for_notification(client: SignifyClient, route: str):
    while True:
        notifications = client.notifications().list()
        for notif in notifications['notes']:
            if notif['a']['r'] == route:
                return notif
        sleep(1)

def admit_credential(client: SignifyClient, name: str, said: str, recipient: str):
    dt = create_timestamp()
    hab = client.identifiers().get(name)

    admit, sigs, end = client.ipex().admit(hab, '', said, dt)

    client.ipex().submitAdmit(name=name, exn=admit, sigs=sigs, atc=end, recp=recipient)


def run():
    issuer_client = connect()
    holder_client = connect()

    print(f"Holder connected agent {holder_client.agent.pre}")
    print(f"Issuer connected agent {issuer_client.agent.pre}")

    issuer_prefix = create_identifier(issuer_client, "issuer")
    holder_prefix = create_identifier(holder_client, "holder")

    print(f"Issuer prefix {issuer_prefix}")
    print(f"Holder prefix {holder_prefix}")

    issuer_oobi = get_agent_oobi(issuer_client, 'issuer')
    holder_oobi = get_agent_oobi(holder_client, 'holder')
    resolve_oobi(issuer_client, holder_oobi, 'holder')
    resolve_oobi(issuer_client, SCHEMA_OOBI, 'schema')
    resolve_oobi(holder_client, issuer_oobi, 'issuer')
    resolve_oobi(holder_client, SCHEMA_OOBI, 'schema')

    registry = create_registry(issuer_client, 'issuer', 'vLEI')
    print(f"Registry created name={registry['name']}, regk={registry['regk']}")

    data = {
        "LEI": "5493001KJTIIGC8Y1R17"
    }

    creds = issue_credential(
        client=issuer_client,
        name='issuer',
        registry_name='vLEI',
        schema=SCHEMA_SAID,
        recipient=holder_prefix,
        data=data)
    
    notification = wait_for_notification(holder_client, '/exn/ipex/grant')
    print(f"Received grant {notification}")

    admit_credential(holder_client, 'holder', notification['a']['d'], issuer_prefix)

    holder_client.notifications().markAsRead(notification['i'])
    print(f"Notification marked!")

    print(f"Listing credentials...")

    credentials = holder_client.credentials().list('holder', filtr={})
    while len(credentials) < 1:
        print('No credentials yet...')
        sleep(1)
  
    print('Succeeded')


if __name__ == "__main__":
    run()
