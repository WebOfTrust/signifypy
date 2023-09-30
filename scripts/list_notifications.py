# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def list_notifications():
    url = "http://localhost:3901"
    bran = b'Pwt6yLXRSs7IjZ23tRHIV'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    notificatons = client.notifications()

    notes = notificatons.list()

    print(notes)


if __name__ == "__main__":
    list_notifications()
