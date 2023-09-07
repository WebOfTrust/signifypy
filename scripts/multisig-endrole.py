# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def stream_escrows():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()

    members = identifiers.members("multisig")

    auths = {}
    for member in members['signing']:
        print(member["aid"])
        ends = member["ends"]

        if not ends:
            print("\tNone")

        if "agent" in ends:
            for k in ends['agent']:

                print("\tAgent: ", k)


    # endroles = client.endroles()
    # print(endroles.list(name="multisig-sigpy"))
    # print(endroles.list(aid="ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V"))

    # escrows = client.escrows()
    #
    # for rpy in escrows.getEscrowReply(route="/end/role"):
    #     print(rpy)


if __name__ == "__main__":
    stream_escrows()
