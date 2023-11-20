# -*- encoding: utf-8 -*-
"""
SIGNIFY
join new quadlet script

"""

from time import sleep

from keri.core import eventing, coring
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def join_new_quadlet():
    group = "multisig"
    client1 = get_client(bran=b'0123456789abcdefghsec')
    client2 = get_client(bran=b'0123456789abcdefghsaw')

    op2 = accept_join_request(client2, name="multisig2", group=group)
    if not op2:
        raise ValueError("No op created for multisig2")
    op1 = accept_join_request(client1, name="multisig1", group=group)
    if not op1:
        raise ValueError("No op created for multisig1")

    while not op2['done']:
        sleep(1)
        op2 = client2.operations().get(op2['name'])

    while not op1['done']:
        sleep(1)
        op1 = client1.operations().get(op1['name'])


def get_client(bran):
    url = "http://localhost:3901"
    tier = Tiers.low

    return SignifyClient(passcode=bran, tier=tier, url=url)


def accept_join_request(client, name, group):
    identifiers = client.identifiers()
    notificatons = client.notifications()
    exchanges = client.exchanges()
    groups = client.groups()

    hab = identifiers.get(name)

    resp = notificatons.list()

    for note in resp['notes']:
        payload = note['a']
        route = payload['r']
        if route == "/multisig/rot":
            said = payload['d']

            res = exchanges.get(said=said)
            exn = res['exn']
            a = exn['a']

            gid = a['gid']
            smids = a['smids']
            rmids = a['rmids']

            recipients = list(set(smids + (rmids or [])))
            recipients.remove(hab['prefix'])

            idx = smids.index(hab["prefix"])
            odx = rmids.index(hab['prefix'])

            embeds = exn['e']
            ked = embeds['rot']
            rot = coring.Serder(ked=ked)

            keeper = client.manager.get(aid=hab)
            sigs = keeper.sign(ser=rot.raw, indexed=True, indices=[idx], ondices=[odx])

            op = groups.join(group, rot, sigs, gid, smids, rmids)

            embeds = dict(
                rot=eventing.messagize(serder=rot, sigers=[coring.Siger(qb64=sig) for sig in sigs])
            )

            exchanges.send(name, "multisig", sender=hab, route="/multisig/rot",
                           payload=dict(gid=gid, smids=smids, rmids=smids),
                           embeds=embeds, recipients=recipients)

            return op

    return None


if __name__ == "__main__":
    join_new_quadlet()
