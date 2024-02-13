# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import sys

from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def send_admit(grant, recp):
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()

    hab = identifiers.get("BankUser")
    create_admit(client, hab, grant, recp)


def create_admit(client, hab, said, recp, dt=None):
    ipex = client.ipex()
    admit, sigs, atc = ipex.admit(hab, "", said, dt=dt)

    ipex.submitAdmit(hab['name'], exn=admit, sigs=sigs, atc=atc, recp=recp)


if __name__ == "__main__":
    send_admit(sys.argv[1], sys.argv[2])
