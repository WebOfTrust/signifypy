# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from keri.core import coring
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def list_notifications():
    url = "http://localhost:3901"
    bran = b'PoLT1X6fDQliXyCuzCVuv'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    notificatons = client.notifications()

    notes = notificatons.list()
    print(notes)

    exchanges = client.exchanges()

    note = notes['notes'][3]
    said = note['a']['d']

    res = exchanges.get("holder1", said)
    exn = coring.Serder(ked=res['exn'])

    print(exn.pretty(size=7000))


if __name__ == "__main__":
    list_notifications()
