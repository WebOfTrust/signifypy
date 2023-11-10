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
    keyStates = client.keyStates()

    multisig1 = keyStates.get("EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4")
    multisig2 = keyStates.get("EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1")

    print(json.dumps([multisig1, multisig2]))


if __name__ == "__main__":
    list_contacts()
