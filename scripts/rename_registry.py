# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import sys

from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def rename_registry(name, registryName, newName):
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghsec'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()
    registries = client.registries()

    hab = identifiers.get(name)

    res = registries.rename(hab, registryName, newName)
    print(res)

    registry = registries.get(hab['name'], newName)
    print(registry)

if __name__ == "__main__":
    rename_registry(sys.argv[1], sys.argv[2], sys.argv[3])
