# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from time import sleep

import requests
from keri import kering
from keri.app import signing
from keri.app.keeping import Algos
from keri.core import coring, eventing, serdering
from keri.core.coring import Tiers
from keri.help import helping

from signify.app.clienting import SignifyClient

TIME = "2023-10-15T16:01:37.000000+00:00"

def multisig_holder():
    print("Creating issuer agent")
    client0 = create_agent(b'Dmopaoe5tANSD8A5rwIhW',
                           "EGTZsyZyREvrD-swB4US5n-1r7h-40sVPIrmS14ixuoJ",
                           "EPkVulMF7So04EJqUDmmHu6SkllpbOt-KJOnSwckmXwz")

    print("Creating issuer AID")
    create_aid(client0, "issuer", "W1OnK0b5rKq6TcKBWhsQa", "ELTkSY_C70Qj8SbPh7F121Q3iA_zNlt8bS-pzOMiCBgG")
    add_end_role(client0, "issuer")
    issuer = get_aid(client0, "issuer")

    print("Creating holder1 agent")
    client1 = create_agent(b'PoLT1X6fDQliXyCuzCVuv',
                           "EBqP5_kfQIsBWPWSKOL0iiaDv-nwVvNsN0YHP7SYKK2u",
                           "ENEDfnaIJyB-ITwEZGv559Mzdk0lNng3UaQKJWzFoTK0")

    print("Creating holder1 AID")
    create_aid(client1, "holder1", "B-GzoqRMFLGtV0Zy0Jajw", "ENIatcaOLTJ3AMCbv0ZiTXR-2HGrJAwsyXVKhQpwuaIq")
    add_end_role(client1, "holder1")

    print("Creating holder2 agent")
    client2 = create_agent(b'Pwt6yLXRSs7IjZ23tRHIV',
                           "EA-SUezF76zn7zF7so-T-DF8FsvI9vO1mtOhWjbdRsqK",
                           "EBn32S-PTYCVZWIhE4jT0l9-23suzNs2z7raYf0YpOSb")
    print("Creating holder2 AID")
    create_aid(client2, "holder2", "AAuXz_5CvLOXMCtZ1prCS", "EBlzZyyDM2wBzPLPKO0RiMGbYJ1PuryD1-zQOr9fKctV")
    add_end_role(client2, "holder2")

    print("Resolving OOBIs")
    holder2 = resolve_oobi(client1, "holder2",
                           "http://127.0.0.1:3902/oobi/EBlzZyyDM2wBzPLPKO0RiMGbYJ1PuryD1-zQOr9fKctV/agent/"
                           "EBn32S-PTYCVZWIhE4jT0l9-23suzNs2z7raYf0YpOSb")
    resolve_oobi(client1, "issuer",
                 "http://127.0.0.1:3902/oobi/ELTkSY_C70Qj8SbPh7F121Q3iA_zNlt8bS-pzOMiCBgG/agent/"
                 "EPkVulMF7So04EJqUDmmHu6SkllpbOt-KJOnSwckmXwz")

    holder1 = resolve_oobi(client2, "holder1",
                           "http://127.0.0.1:3902/oobi/ENIatcaOLTJ3AMCbv0ZiTXR-2HGrJAwsyXVKhQpwuaIq/agent/"
                           "ENEDfnaIJyB-ITwEZGv559Mzdk0lNng3UaQKJWzFoTK0")
    resolve_oobi(client2, "issuer",
                 "http://127.0.0.1:3902/oobi/ELTkSY_C70Qj8SbPh7F121Q3iA_zNlt8bS-pzOMiCBgG/agent/"
                 "EPkVulMF7So04EJqUDmmHu6SkllpbOt-KJOnSwckmXwz")

    resolve_oobi(client0, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    resolve_oobi(client1, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    resolve_oobi(client2, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")

    words = client1.challenges().generate()
    print(f"Challenging holder1 with {words}")
    client2.challenges().respond("holder2", holder1['i'], words)

    op = client1.challenges().verify("holder1", holder2['i'], words)
    while not op["done"]:
        op = client1.operations().get(op['name'])
        sleep(1)

    exn = serdering.SerderKERI(sad=op["response"]['exn'])
    print(f"Challenge signed in {exn.said}")
    client1.challenges().responded("holder1", holder2['i'], exn.said)

    states = [holder1, holder2]

    member1 = get_aid(client1, "holder1")
    member2 = get_aid(client2, "holder2")

    op1 = create_multisig(client1, "holder", member1, states)
    op2 = create_multisig(client2, "holder", member2, states)

    gaid1 = wait_on_operation(client1, op1)
    print(f"{gaid1['i']} created for holder1")
    gaid2 = wait_on_operation(client2, op2)
    print(f"{gaid2['i']} created for holder2")

    ghab1 = client1.identifiers().get("holder")
    ghab2 = client2.identifiers().get("holder")

    stamp = helping.nowIso8601()
    add_end_role_multisig(client1, "holder", ghab1, member1, client1.agent.pre, stamp=stamp)
    op1 = add_end_role_multisig(client2, "holder", ghab2, member2, client1.agent.pre, stamp=stamp)
    add_end_role_multisig(client1, "holder", ghab1, member1, client2.agent.pre, stamp=stamp)
    op2 = add_end_role_multisig(client2, "holder", ghab2, member2, client2.agent.pre, stamp=stamp)

    while not op1["done"]:
        op1 = client1.operations().get(op1['name'])
        sleep(1)

    while not op2["done"]:
        op2 = client1.operations().get(op2['name'])
        sleep(1)

    holder = resolve_oobi(client0, "holder", "http://127.0.0.1:3902/oobi/EH_axvx0v0gwQaCawqem5u8ZeDKx9TUWKsowTa_xj0yb")

    create_credential(client0, holder)

    notificatons = client1.notifications()

    notes = notificatons.list()
    while notes['total'] < 4:
        sleep(1)
        notes = notificatons.list()

    grant = notes['notes'][3]
    gsaid = grant['a']['d']
    print(f"Received grant notification for grant {gsaid}")

    print(f"\nSending admit back")
    create_admit(client1, "holder1", "holder", gsaid, [member2['prefix']])
    create_admit(client2, "holder2", "holder", gsaid, [member1['prefix']])

    notificatons = client0.notifications()

    notes = notificatons.list()
    while notes['total'] < 1:
        sleep(1)
        notes = notificatons.list()

    print(f"\nissuer notifications..")
    print(notes)

    print(f"\nChecking credentials for holder1...")
    credentials = client1.credentials().list()
    while len(credentials) < 1:
        print('  No credentials yet...')
        sleep(1)
        credentials = client1.credentials().list()

    print('holder1 recieved credential: ')
    creder = serdering.SerderACDC(sad=credentials[0]['sad'])
    print(creder.pretty(size=5000))

def create_agent(bran, controller, agent):
    url = "http://localhost:3901"
    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == controller

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

    client.connect(url=url, )
    assert client.agent is not None
    print("Agent created:")
    print(f"    Agent: {client.agent.pre}    Controller: {client.agent.delpre}")
    assert client.agent.pre == agent
    assert client.agent.delpre == controller
    return client


def create_aid(client, name, bran, expected):
    identifiers = client.identifiers()
    (_, _, op) = identifiers.create(name, bran=bran)
    icp = op["response"]
    serder = serdering.SerderKERI(sad=icp)
    assert serder.pre == expected
    print(f"AID Created: {serder.pre}")


def resolve_oobi(client, alias, url):
    oobis = client.oobis()
    operations = client.operations()

    op = oobis.resolve(oobi=url,
                       alias=alias)

    print(f"resolving oobi for {alias}")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    print("... done")
    return op["response"]


def create_multisig(client, name, member, states):
    identifiers = client.identifiers()
    exchanges = client.exchanges()

    icp, isigs, op = identifiers.create(name, algo=Algos.group, mhab=member,
                                        isith=["1/2", "1/2"], nsith=["1/2", "1/2"],
                                        states=states,
                                        rstates=states)

    smids = [state['i'] for state in states]
    recps = [x['i'] for x in states if x['i'] != member['prefix']]

    embeds = dict(
        icp=eventing.messagize(serder=icp, sigers=[coring.Siger(qb64=sig) for sig in isigs])
    )

    exchanges.send(member['name'], "multisig", sender=member, route="/multisig/icp",
                   payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                   embeds=embeds, recipients=recps)

    return op


def create_admit(client, participant, group, said, recp):
    exchanges = client.exchanges()
    ipex = client.ipex()

    res = exchanges.get(said)
    grant = serdering.SerderKERI(sad=res['exn'])
    ghab = get_aid(client, group)
    mhab = get_aid(client, participant)

    admit, sigs, end = ipex.admit(ghab, "", said, dt=TIME)

    mstate = ghab["state"]
    seal = eventing.SealEvent(i=ghab["prefix"], s=mstate["ee"]["s"], d=mstate["ee"]["d"])
    ims = eventing.messagize(serder=admit, sigers=[coring.Siger(qb64=sig) for sig in sigs], seal=seal)
    ims.extend(end)
    embeds = dict(
        exn=ims
    )
    atc = bytes(ims[admit.size:])

    exchanges.send(participant, "multisig", sender=mhab, route="/multisig/exn",
                   payload=dict(gid=ghab["prefix"]),
                   embeds=embeds, recipients=recp)

    ipex.submitAdmit(ghab['name'], exn=admit, sigs=sigs, atc=end, recp=[grant.ked['i']])


def get_aid(client, name):
    identifiers = client.identifiers()
    return identifiers.get(name)


def wait_on_operation(client, op):
    operations = client.operations()
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    return op["response"]


def add_end_role(client, name):
    identifiers = client.identifiers()
    identifiers.addEndRole(name, eid=client.agent.pre)


def add_end_role_multisig(client, name, ghab, m, eid, stamp=None):
    exchanges = client.exchanges()
    identifiers = client.identifiers()

    rpy, sigs, op = identifiers.addEndRole(name, eid=eid, stamp=stamp)

    gstate = ghab["state"]
    seal = eventing.SealEvent(i=ghab["prefix"], s=gstate["ee"]["s"], d=gstate["ee"]["d"])
    ims = eventing.messagize(serder=rpy, sigers=[coring.Siger(qb64=sig) for sig in sigs], seal=seal)
    embeds = dict(
        rpy=ims
    )

    members = identifiers.members(name)
    recps = []
    for member in members['signing']:
        recp = member['aid']
        if recp == m['prefix']:
            continue

        recps.append(recp)

    exn, _, _ = exchanges.send(m['name'], "multisig", sender=m, route="/multisig/rpy",
                               payload=dict(gid=ghab['prefix']),
                               embeds=embeds, recipients=recps)

    return op


def create_credential(client, holder):
    registries = client.registries()
    identifiers = client.identifiers()
    credentials = client.credentials()
    operations = client.operations()
    ipex = client.ipex()
    exchanges = client.exchanges()

    issuer = identifiers.get("issuer")

    print("Creating vLEI Registry")
    _, _, _, op = registries.create(hab=issuer, registryName="vLEI")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... created")

    issuer = identifiers.get("issuer")
    registry = registries.get(name="issuer", registryName="vLEI")
    data = {
        "LEI": "5493001KJTIIGC8Y1R17"
    }
    creder, iserder, anc, sigs, op = credentials.create(issuer, registry, data=data,
                                                        schema="EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                                                        recipient=holder['i'])
    print(f"Creating credential {creder.said}")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... created")

    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said))
    iss = registries.serialize(iserder, anc)

    grant, sigs, end = ipex.grant(issuer, recp=holder['i'], acdc=acdc,
                                  iss=iss, message="",
                                  anc=eventing.messagize(serder=anc, sigers=[coring.Siger(qb64=sig) for sig in sigs]))
    print(f"Sending grant {grant.said}")
    exchanges.sendFromEvents("issuer", "credential", grant, sigs, end, [holder['i']])
    print("... sent")


if __name__ == "__main__":
    multisig_holder()
