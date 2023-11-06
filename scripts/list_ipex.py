# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import sys

from keri.core.coring import Tiers
from keri.vc.proving import Creder

from signify.app.clienting import SignifyClient


def list_ipex():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    notificatons = client.notifications()

    notes = notificatons.list()
    for note in notes["notes"]:
        a = note['a']
        if a['r'].startswith("/exn/ipex/"):
            print(a['d'])


if __name__ == "__main__":
    list_ipex()
