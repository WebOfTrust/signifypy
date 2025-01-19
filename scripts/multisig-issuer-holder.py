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
from keri.core import signing as csigning
from keri.core.coring import Tiers
from keri.help import helping

from signify.app.clienting import SignifyClient

TIME = "2023-10-15T16:01:37.000000+00:00"


def multisig_holder():
    print("Creating issuer0 agent")
    client0 = create_agent(b'Dmopaoe5tANSD8A5rwIhW',
                           "EGTZsyZyREvrD-swB4US5n-1r7h-40sVPIrmS14ixuoJ",
                           "EPkVulMF7So04EJqUDmmHu6SkllpbOt-KJOnSwckmXwz")

    print("\nCreating issuer0 AID")
    create_aid(client0, "issuer0", "W1OnK0b5rKq6TcKBWhsQa", "ELTkSY_C70Qj8SbPh7F121Q3iA_zNlt8bS-pzOMiCBgG")
    add_end_role(client0, "issuer0")
    issuer0 = get_aid(client0, "issuer0")
    issuer0Pre = issuer0["prefix"]

    print("\nCreating issuer1 agent")
    client1 = create_agent(b'Dmopaoe5tANSD8A5rwABC',
                           "ECJhEr1SBaNw2MkT0_4P5VivE5Olwvmhh2XH1Q7RGiRM",
                           "ELe_fMsUL54-_jcDRYPa-ln_dGWFOMPt0sJyXaBf0m8G")

    print("\nCreating issuer1 AID")
    create_aid(client1, "issuer1", "W1OnK0b5rKq6TcKBWhsQX", "EFEZBelGfEsFWssz28VZcNNh4bZDsm30UnvDIb3IoI2o")
    add_end_role(client1, "issuer1")
    issuer1 = get_aid(client1, "issuer1")
    issuer1Pre = issuer1["prefix"]

    print("\nResolving Issuer participant OOBIs with each other")
    issuer1 = resolve_oobi(client0, "issuer1",
                           "http://127.0.0.1:3902/oobi/EFEZBelGfEsFWssz28VZcNNh4bZDsm30UnvDIb3IoI2o/agent/"
                           "ELe_fMsUL54-_jcDRYPa-ln_dGWFOMPt0sJyXaBf0m8G")

    issuer0 = resolve_oobi(client1, "issuer0",
                           "http://127.0.0.1:3902/oobi/ELTkSY_C70Qj8SbPh7F121Q3iA_zNlt8bS-pzOMiCBgG/agent/"
                           "EPkVulMF7So04EJqUDmmHu6SkllpbOt-KJOnSwckmXwz")

    print("\nCreating Issuer Mutlsig AID")
    states = [issuer0, issuer1]

    member1 = get_aid(client0, "issuer0")
    member2 = get_aid(client1, "issuer1")

    op1 = create_multisig(client0, "issuer", member1, states)
    op2 = create_multisig(client1, "issuer", member2, states)

    gaid1 = wait_on_operation(client0, op1)
    print(f"{gaid1['i']} created for issuer0")
    gaid2 = wait_on_operation(client1, op2)
    print(f"{gaid2['i']} created for issuer1")

    print("\nAuthorizing agent endpoints for Issuer Multisig")
    ighab1 = client0.identifiers().get("issuer")
    ighab2 = client1.identifiers().get("issuer")

    stamp = helping.nowIso8601()
    add_end_role_multisig(client0, "issuer", ighab1, member1, client1.agent.pre, stamp=stamp)
    op1 = add_end_role_multisig(client1, "issuer", ighab2, member2, client1.agent.pre, stamp=stamp)
    add_end_role_multisig(client0, "issuer", ighab1, member1, client1.agent.pre, stamp=stamp)
    op2 = add_end_role_multisig(client1, "issuer", ighab2, member2, client1.agent.pre, stamp=stamp)

    while not op1["done"]:
        op1 = client1.operations().get(op1['name'])
        sleep(0.25)

    while not op2["done"]:
        op2 = client1.operations().get(op2['name'])
        sleep(0.25)

    print("\nCreating holder0 agent")
    hclient0 = create_agent(b'PoLT1X6fDQliXyCuzCVuv',
                            "EBqP5_kfQIsBWPWSKOL0iiaDv-nwVvNsN0YHP7SYKK2u",
                            "ENEDfnaIJyB-ITwEZGv559Mzdk0lNng3UaQKJWzFoTK0")

    print("\nCreating holder0 AID")
    create_aid(hclient0, "holder0", "B-GzoqRMFLGtV0Zy0Jajw", "ENIatcaOLTJ3AMCbv0ZiTXR-2HGrJAwsyXVKhQpwuaIq")
    add_end_role(hclient0, "holder0")
    holder0 = get_aid(hclient0, "holder0")
    holder0Pre = holder0["prefix"]

    print("\nCreating holder1 agent")
    hclient1 = create_agent(b'Pwt6yLXRSs7IjZ23tRHIV',
                            "EA-SUezF76zn7zF7so-T-DF8FsvI9vO1mtOhWjbdRsqK",
                            "EBn32S-PTYCVZWIhE4jT0l9-23suzNs2z7raYf0YpOSb")
    print("\nCreating holder1 AID")
    create_aid(hclient1, "holder1", "AAuXz_5CvLOXMCtZ1prCS", "EBlzZyyDM2wBzPLPKO0RiMGbYJ1PuryD1-zQOr9fKctV")
    add_end_role(hclient1, "holder1")
    holder1 = get_aid(hclient1, "holder1")
    holder1Pre = holder1["prefix"]

    print("\nResolving Holder participant OOBIs with each other")
    holder1 = resolve_oobi(hclient0, "holder1",
                           "http://127.0.0.1:3902/oobi/EBlzZyyDM2wBzPLPKO0RiMGbYJ1PuryD1-zQOr9fKctV/agent/"
                           "EBn32S-PTYCVZWIhE4jT0l9-23suzNs2z7raYf0YpOSb")

    holder0 = resolve_oobi(hclient1, "holder0",
                           "http://127.0.0.1:3902/oobi/ENIatcaOLTJ3AMCbv0ZiTXR-2HGrJAwsyXVKhQpwuaIq/agent/"
                           "ENEDfnaIJyB-ITwEZGv559Mzdk0lNng3UaQKJWzFoTK0")

    resolve_oobi(client0, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    resolve_oobi(client1, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    resolve_oobi(hclient0, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    resolve_oobi(hclient1, "vc", "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")

    words = hclient0.challenges().generate()
    print(f"\nChallenging holder0 with {words}")
    hclient1.challenges().respond("holder1", holder0['i'], words)

    op = hclient0.challenges().verify("holder0", holder1['i'], words)
    while not op["done"]:
        op = hclient0.operations().get(op['name'])
        sleep(0.25)

    exn = serdering.SerderKERI(sad=op["response"]['exn'])
    print(f"\nChallenge signed in {exn.said}")
    hclient0.challenges().responded("holder0", holder1['i'], exn.said)

    states = [holder0, holder1]

    member1 = get_aid(hclient0, "holder0")
    member2 = get_aid(hclient1, "holder1")

    op1 = create_multisig(hclient0, "holder", member1, states)
    op2 = create_multisig(hclient1, "holder", member2, states)

    gaid1 = wait_on_operation(hclient0, op1)
    print(f"{gaid1['i']} created for holder0")
    gaid2 = wait_on_operation(hclient1, op2)
    print(f"{gaid2['i']} created for holder1")

    ghab1 = hclient0.identifiers().get("holder")
    ghab2 = hclient1.identifiers().get("holder")

    stamp = helping.nowIso8601()
    add_end_role_multisig(hclient0, "holder", ghab1, member1, hclient0.agent.pre, stamp=stamp)
    op1 = add_end_role_multisig(hclient1, "holder", ghab2, member2, hclient0.agent.pre, stamp=stamp)
    add_end_role_multisig(hclient0, "holder", ghab1, member1, hclient1.agent.pre, stamp=stamp)
    op2 = add_end_role_multisig(hclient1, "holder", ghab2, member2, hclient1.agent.pre, stamp=stamp)

    while not op1["done"]:
        op1 = hclient1.operations().get(op1['name'])
        sleep(0.25)

    while not op2["done"]:
        op2 = hclient1.operations().get(op2['name'])
        sleep(0.25)

    resolve_oobi(client0, "holder", "http://127.0.0.1:3902/oobi/EH_axvx0v0gwQaCawqem5u8ZeDKx9TUWKsowTa_xj0yb")
    holder = resolve_oobi(client1, "holder", "http://127.0.0.1:3902/oobi/EH_axvx0v0gwQaCawqem5u8ZeDKx9TUWKsowTa_xj0yb")

    resolve_oobi(hclient0, "issuer", "http://127.0.0.1:3902/oobi/EHJxS_kEeS9RLZhdgHvA6imWzw4OkQ-VRNlX7HIt-9T9")
    issuer = resolve_oobi(hclient0, "issuer", "http://127.0.0.1:3902/oobi/EHJxS_kEeS9RLZhdgHvA6imWzw4OkQ-VRNlX7HIt-9T9")

    print("\nCreating Credential Registry for Multisig Issuer")
    op1 = create_registry(client0, "issuer0", "issuer", [issuer1Pre], "vLEI",
                          "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s")
    op2 = create_registry(client1, "issuer1", "issuer", [issuer0Pre], "vLEI",
                          "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s")
    while not op1["done"]:
        op1 = client0.operations().get(op1['name'])
        sleep(0.25)

    while not op2["done"]:
        op2 = client1.operations().get(op2['name'])
        sleep(0.25)

    print("\nCreating Credential from Multisig Issuer")
    stamp = helping.nowIso8601()
    creder, iserder, anc, sigs, op1 = create_credential(client0, "issuer0", "issuer",
                                                        [issuer1Pre], "vLEI", holder['i'], stamp)
    creder, iserder, anc, sigs, op2 = create_credential(client1, "issuer1", "issuer",
                                                        [issuer0Pre], "vLEI", holder['i'], stamp)
    while not op1["done"]:
        op1 = client0.operations().get(op1['name'])
        sleep(0.25)

    while not op2["done"]:
        op2 = client1.operations().get(op2['name'])
        sleep(0.25)

    print("\nSend GRANT from Multisig Issuer to Multisig Holder")
    op1 = create_grant(client0, "issuer0", "issuer", creder, iserder, anc, sigs, [issuer1Pre], holder['i'], stamp)
    op2 = create_grant(client1, "issuer1", "issuer", creder, iserder, anc, sigs, [issuer0Pre], holder['i'], stamp)
    while not op1["done"]:
        op1 = client0.operations().get(op1['name'])
        sleep(0.25)

    while not op2["done"]:
        op2 = client1.operations().get(op2['name'])
        sleep(0.25)

    notificatons = hclient0.notifications()

    notes = notificatons.list()
    while notes['total'] < 4:
        sleep(3)
        notes = notificatons.list()

    grant = notes['notes'][-1]
    gsaid = grant['a']['d']
    print(f"Received grant notification for grant {gsaid}")

    print(f"\nSending admit back")
    create_admit(hclient0, "holder0", "holder", gsaid, [holder1Pre], stamp)
    create_admit(hclient1, "holder1", "holder", gsaid, [holder0Pre], stamp)

    notificatons = client0.notifications()

    notes = notificatons.list()
    while notes['total'] < 1:
        sleep(1)
        notes = notificatons.list()

    print(f"\nChecking credentials for holder0...")
    credentials = hclient0.credentials().list()
    while len(credentials) < 1:
        print('  No credentials yet...')
        sleep(1)
        credentials = hclient0.credentials().list()

    print('holder0 recieved credential: ')
    creder = serdering.SerderACDC(sad=credentials[0]['sad'])
    print(creder.pretty(size=5000))


def create_agent(bran, controller, agent):
    url = "http://localhost:3901"
    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == controller, f"not {client.controller}"

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
    assert client.agent.pre == agent, f"not {client.agent.pre}"
    assert client.agent.delpre == controller
    return client


def create_aid(client, name, bran, expected):
    identifiers = client.identifiers()
    (_, _, op) = identifiers.create(name, bran=bran)
    icp = op["response"]
    serder = serdering.SerderKERI(sad=icp)
    assert serder.pre == expected, f"not {serder.pre}"
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
        icp=eventing.messagize(serder=icp, sigers=[csigning.Siger(qb64=sig) for sig in isigs])
    )

    exchanges.send(member['name'], "multisig", sender=member, route="/multisig/icp",
                   payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                   embeds=embeds, recipients=recps)

    return op


def create_admit(client, participant, group, said, recp, stamp):
    exchanges = client.exchanges()
    ipex = client.ipex()

    res = exchanges.get(said)
    grant = serdering.SerderKERI(sad=res['exn'])
    ghab = get_aid(client, group)
    mhab = get_aid(client, participant)

    admit, sigs, end = ipex.admit(ghab, "", said, dt=stamp)

    print(f"created ADMIT {admit.said}")
    mstate = ghab["state"]
    seal = eventing.SealEvent(i=ghab["prefix"], s=mstate["ee"]["s"], d=mstate["ee"]["d"])
    ims = eventing.messagize(serder=admit, sigers=[csigning.Siger(qb64=sig) for sig in sigs], seal=seal)
    ims.extend(end)
    embeds = dict(
        exn=ims
    )

    exn, gsigs, end = exchanges.createExchangeMessage(sender=mhab, route="/multisig/exn",
                                                      payload=dict(gid=ghab["prefix"]),
                                                      embeds=embeds)

    ipex.submitAdmit(ghab['name'], exn=exn, sigs=gsigs, atc=end, recp=recp)


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
    ims = eventing.messagize(serder=rpy, sigers=[csigning.Siger(qb64=sig) for sig in sigs], seal=seal)
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


def create_registry(client, localName, groupName, recp, name, nonce):
    registries = client.registries()
    identifiers = client.identifiers()
    exchanges = client.exchanges()

    group = identifiers.get(groupName)
    local = identifiers.get(localName)

    print("Creating vLEI Registry")
    vcp, anc, rsigs, op = registries.create(hab=group, registryName=name,
                                            nonce=nonce)

    embeds = dict(
        vcp=vcp.raw,
        anc=eventing.messagize(serder=anc, sigers=[csigning.Siger(qb64=sig) for sig in rsigs])
    )

    exchanges.send(localName, groupName, sender=local, route="/multisig/vcp",
                   payload=dict(gid=group["prefix"], usage="Issue vLEIs"),
                   embeds=embeds, recipients=recp)

    return op


def create_credential(client, localName, groupName, recp, registryName, holder, stamp):
    registries = client.registries()
    identifiers = client.identifiers()
    credentials = client.credentials()
    exchanges = client.exchanges()

    issuer = identifiers.get(groupName)
    local = identifiers.get(localName)

    registry = registries.get(name=groupName, registryName=registryName)
    data = {
        "LEI": "5493001KJTIIGC8Y1R17"
    }
    creder, iserder, anc, sigs, op = credentials.create(issuer, registry, data=data,
                                                        schema="EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                                                        recipient=holder, timestamp=stamp)
    print(f"Creating credential {creder.said}")
    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said))
    iss = registries.serialize(iserder, anc)

    embeds = dict(
        acdc=acdc,
        iss=iss,
        anc=eventing.messagize(serder=anc, sigers=[csigning.Siger(qb64=sig) for sig in sigs])
    )
    exchanges.send(localName, groupName, sender=local, route="/multisig/iss",
                   payload=dict(gid=issuer["prefix"]),
                   embeds=embeds, recipients=recp)

    return creder, iserder, anc, sigs, op


def create_grant(client, localName, groupName, creder, iserder, anc, sigs, recp, holder, stamp):
    identifiers = client.identifiers()
    ipex = client.ipex()
    registries = client.registries()
    exchanges = client.exchanges()

    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said))
    iss = registries.serialize(iserder, anc)

    issuer = identifiers.get(groupName)
    local = identifiers.get(localName)

    grant, sigs, end = ipex.grant(issuer, recp=holder, acdc=acdc,
                                  iss=iss, message="", dt=stamp,
                                  anc=eventing.messagize(serder=anc, sigers=[csigning.Siger(qb64=sig) for sig in sigs]))

    print(f'created grant {grant.said}')
    mstate = issuer["state"]
    seal = eventing.SealEvent(i=issuer["prefix"], s=mstate["ee"]["s"], d=mstate["ee"]["d"])
    ims = eventing.messagize(serder=grant, sigers=[csigning.Siger(qb64=sig) for sig in sigs], seal=seal)
    ims.extend(end.encode("utf-8"))
    embeds = dict(
        exn=ims
    )

    exn, gsigs, end = exchanges.createExchangeMessage(sender=local, route="/multisig/exn",
                                                      payload=dict(gid=issuer["prefix"]),
                                                      embeds=embeds)

    op = ipex.submitGrant(issuer['name'], exn=exn, sigs=gsigs, atc=end, recp=recp)
    return op


if __name__ == "__main__":
    multisig_holder()
