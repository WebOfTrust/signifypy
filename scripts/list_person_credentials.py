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
    # bran = b'0123456789abcdefghijk'
    # bran = b'PoLT1X6fDQliXyCuzCVuv'
    bran = b'Pwt6yLXRSs7IjZ23tRHIV'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    res = identifiers.list()

    aids = res['aids']

    assert len(aids) == 2

    res = identifiers.get("holder")

    aid = res['prefix']
    print(aid)
    credentials = client.credentials()

    creds = credentials.list(filtr={'-a-i': aid})
    # print(creds)
    assert len(creds) == 1

    creder = serdering.SerderACDC(sad=creds[0]['sad'])
    print(creder.pretty(size=5000))

    # said = creder.said
    # print(f"Exporting credential {said}")
    # export = credentials.export("BankUser", said)
    # print(export)


if __name__ == "__main__":
    list_credentials()
