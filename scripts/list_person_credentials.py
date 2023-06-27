# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

from keri.core.coring import Tiers
from keri.vc.proving import Creder

from signify.app.clienting import SignifyClient
from signify.app.credentialing import CredentialTypes


def list_credentials():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    credentials = client.credentials(aid="EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk")

    creds = credentials.list(typ=CredentialTypes.received)
    assert len(creds) == 1

    creder = Creder(ked=creds[0]['sad'])
    said = creder.said

    print(f"Exporting credential {said}")

    export = credentials.export("aid1", said)
    print(export)


if __name__ == "__main__":
    list_credentials("aid1")
