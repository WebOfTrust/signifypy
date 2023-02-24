# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json

import pytest
from keri import kering
from keri.core.coring import Tiers, Serder

from signify.app.clienting import SignifyClient


def test_init():
    url = "http://localhost:5632"
    bran = b'0123456789abcdefghijk'
    tier = None
    temp = True

    # Try with bran that is too short
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url=url, bran=bran[:16], tier=tier, temp=temp)

    # Try with an invalid URL
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url="ftp://www.example.com", bran=bran, tier=tier, temp=temp)

    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EA0jffuFfGdPBcV1urlKtM9O5XZgRttQrKNVFtB30c13"

    # changing tier with Temp=True has no effect
    tier = Tiers.low
    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EA0jffuFfGdPBcV1urlKtM9O5XZgRttQrKNVFtB30c13"

    temp = False
    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EH47SaIWwMbBh3P39AFP-qe-J87-Z-gcj-ZUJ7uyplHF"

    tier = Tiers.med
    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EFrCn76IOMVENbf8EZFXCE3s9HEHQK7Xq93GLAEr9Voo"

    tier = Tiers.high
    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EEu7aTxB4PbQY4sF72Lc-QjwcQuuAL_zRnHJGEj3Ca6b"


def test_connect():
    """ This test assumes a running KERIA agent with the following comand:

          `keria start -c EH47SaIWwMbBh3P39AFP-qe-J87-Z-gcj-ZUJ7uyplHF`

    """
    url = "http://localhost:5632"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low
    temp = True

    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EA0jffuFfGdPBcV1urlKtM9O5XZgRttQrKNVFtB30c13"

    # Raises configuration error because the started agent has a different controller AID
    with pytest.raises(kering.ConfigurationError):
        client.connect()

    temp = False
    client = SignifyClient(url=url, bran=bran, tier=tier, temp=temp)
    assert client.controller == "EH47SaIWwMbBh3P39AFP-qe-J87-Z-gcj-ZUJ7uyplHF"

    client.connect()
    assert client.agent is not None
    assert client.agent.anchor == "EH47SaIWwMbBh3P39AFP-qe-J87-Z-gcj-ZUJ7uyplHF"
    assert client.agent.pre == "EPumlwOcIn_vbxTDz6Vr4Q6bEwWLReDhForDu_HqWRyx"
    assert client.ctrl.ridx == 0

    identifiers = client.identifiers()
    aids = identifiers.list()
    assert aids == []

    aid = identifiers.create("aid1")
    icp = Serder(ked=aid)
    assert icp.pre == "EEc0pzAa0xtxkoW5Dr_i9F2n0Gsq70BeYpnBjuFujWbL"
    assert len(icp.verfers) == 1
    assert icp.verfers[0].qb64 == "DF42EWnAQVw7izQsjVkrISSKIkAQMY8-MpmKA1wyxx7-"
    assert len(icp.digers) == 1
    assert icp.digers[0].qb64 == "EOgh4EcRDrdf5_2DnmQnWZ3AeHytpEV6bC6nlLCfFQOF"
    assert icp.tholder.num == 1
    assert icp.ntholder.num == 1

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()

    assert aid['name'] == "aid1"
    assert aid["pidx"] == 0
    assert aid["prefix"] == icp.pre
    assert aid["stem"] == "signify:aid"
    assert aid["temp"] is False

    aid2 = identifiers.create("aid2", temp=True, count=3, ncount=3, isith="2", nsith="2")
    icp2 = Serder(ked=aid2)
    assert icp2.pre == "ECuO44S--iT4xank5-h1-EJ8SudTv_YH76lxGc479hvX"
    assert len(icp2.verfers) == 3
    assert icp2.verfers[0].qb64 == "DHLvq6b2sPgj-1HXId-0K1-zgsm0t1BTVPZy8gWQRAWW"
    assert icp2.verfers[1].qb64 == "DIDfa8QTglW-6nCEe0zLfGTiILudaa1wFhOOo1iOKcxn"
    assert icp2.verfers[2].qb64 == "DH9R9rA9n1Flre2Zwc9mMIsgCzqKra40DC9EwZq6tjUU"
    assert len(icp2.digers) == 3
    assert icp2.digers[0].qb64 == "EIWbtiKgM3TUKx9hrzNVnCxCbc38TGViMD_W_F1qlA-I"
    assert icp2.digers[1].qb64 == "EB5xAamY0CQMOZWvZWRJX6KkhsWrCH8bz2-Fmiacm7sV"
    assert icp2.digers[2].qb64 == "EJ7Q350565TB7l3JO-2Do_JSacYAXhGwFUrHqrwqbShv"
    assert icp2.tholder.num == 2
    assert icp2.ntholder.num == 2

    aids = identifiers.list()
    assert len(aids) == 2
    aid = aids[1]
    assert aid['name'] == "aid2"
    assert aid["pidx"] == 1
    assert aid["prefix"] == icp2.pre
    assert aid["stem"] == "signify:aid"
    assert aid["temp"] is True

    ked = identifiers.rotate("aid1")
    rot = Serder(ked=ked)

    assert rot.said == "EJGHEadqsS7c0Cr1cayAAmEwvLQ2l1IrVQcVORGqNcx2"
    assert rot.sn == 1
    assert len(rot.digers) == 1
    assert rot.digers[0].qb64 == "EJaC2SqhqULqYOSzr8Jy_Vavi06Tt0YtWqNAFaQ_9GOa"

    ked = identifiers.interact("aid1", data=[icp.pre])
    ixn = Serder(ked=ked)
    assert ixn.said == "EBwiEGe7LEoLlH1nwFVBRBkb7xGgAbLinMfdjNOQsX8O"
    assert ixn.sn == 2
    assert ixn.ked["a"] == [icp.pre]