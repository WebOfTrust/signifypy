from time import sleep

import requests
from keri import kering
from keri.app.keeping import Algos
from keri.core import eventing, signing, serdering
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def create_multisig():
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

    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()
    exchanges = client.exchanges()

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
        icp=eventing.messagize(serder=icp, sigers=[signing.Siger(qb64=sig) for sig in isigs])
    )

    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/icp",
                   payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                   embeds=embeds, recipients=recp)

    print("waiting on multisig creation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    gid = op["response"]
    print(f"group multisig created {gid}")

    # Join an interaction event with the group
    data = {"i": "EE77q3_zWb5ojgJr-R1vzsL5yiL4Nzm-bfSOQzQl02dy"}
    ixn, xsigs, op = identifiers.interact("multisig", data=data)

    embeds = dict(
        ixn=eventing.messagize(serder=ixn, sigers=[signing.Siger(qb64=sig) for sig in xsigs])
    )

    exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/ixn",
                   payload=dict(gid=icp.pre, smids=smids),
                   embeds=embeds, recipients=recp)

    print("waiting for ixn to finish...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    ixn = serdering.SerderKERI(sad=op["response"])
    events = client.keyEvents()
    log = events.get(pre=ixn.pre)
    assert len(log) == 2

    for event in log:
        print(serdering.SerderKERI(sad=event).pretty())

    (_, _, op2) = identifiers.rotate("multisig3")
    rot = op2["response"]
    serder = serdering.SerderKERI(sad=rot)
    print(f"rotated multisig3 to {serder.sn}")

    input("hit any key when other two participants have rotated their AIDs")

    m3 = identifiers.get("multisig3")
    agent0 = m3["state"]

    keyState = client.keyStates()
    op = keyState.query(pre="EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1", sn=1)
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    multisig2 = op["response"]
    print(f"using key {multisig2['k'][0]}")
    print(f"using dig {multisig2['n'][0]}")

    op = keyState.query(pre="EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4", sn=1)
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    multisig1 = op["response"]
    print(f"using key {multisig1['k'][0]}")
    print(f"using dig {multisig1['n'][0]}")

    states = rstates = [multisig1, multisig2, agent0]

    rot, rsigs, op = identifiers.rotate("multisig", states=states, rstates=rstates)
    embeds = dict(
        rot=eventing.messagize(serder=rot, sigers=[signing.Siger(qb64=sig) for sig in rsigs])
    )

    smids = [state['i'] for state in states]
    recp = [state['i'] for state in [multisig1, multisig2]]

    rexn, _, _ = exchanges.send("multisig3", "multisig", sender=m3, route="/multisig/rot",
                                payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                                embeds=embeds, recipients=recp)

    print(rexn.pretty(size=5000))
    print("Waiting for multisig rotation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)


if __name__ == "__main__":
    create_multisig()
