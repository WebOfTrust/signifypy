# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from keri.core import serdering
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def list_credentials():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghsec'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    res = identifiers.list()

    aids = res['aids']

    assert len(aids) == 2

    res = identifiers.get("multisig")

    aid = res['prefix']
    print(aid)
    credentials = client.credentials()

    creds = credentials.list(filtr={'-i': aid})
    for cred in creds:
        creder = serdering.SerderACDC(sad=cred['sad'])
        print(creder.pretty(size=5000))


if __name__ == "__main__":
    list_credentials()
