# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json

from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def list_contacts():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghsaw'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    contacts = client.contacts()

    cons = contacts.list()

    print(json.dumps(cons))


if __name__ == "__main__":
    list_contacts()
