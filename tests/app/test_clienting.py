# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import os
from time import sleep
import responses

import pytest
from keri import kering
from keri.core.coring import Tiers, Serder

from signify.app.clienting import SignifyClient

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_init():
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = None

    # Try with bran that is too short
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url=url, passcode=bran[:16], tier=tier)

    # Try with an invalid URL
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url="ftp://www.example.com", passcode=bran, tier=tier)

    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    tier = Tiers.low
    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    tier = Tiers.med
    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"

    tier = Tiers.high
    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "EB8wN2c_tv1WlsJ5c3949-TFWPMB2IflFbdMlZfC_Hgo"


@responses.activate
def test_connect():
    responses._add_from_file(file_path=os.path.join(TEST_DIR, "connect.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    ctrl = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == ctrl

    agentPre = "EJoqUMpQAfqsJhBqv02ehR-9BJYBTCrW8h5JlLdMTWBg"
    client.connect()
    assert client.agent is not None
    assert client.agent.delpre == ctrl
    assert client.agent.pre == agentPre
    assert client.ctrl.ridx == 0

    identifiers = client.identifiers()
    aids = identifiers.list()
    assert aids == []

    aid = identifiers.create("aid1")
    icp = Serder(ked=aid)
    assert icp.pre == "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"
    assert len(icp.verfers) == 1
    assert icp.verfers[0].qb64 == "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
    assert len(icp.digers) == 1
    assert icp.digers[0].qb64 == "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"
    assert icp.tholder.num == 1
    assert icp.ntholder.num == 1

    rpy = identifiers.makeEndRole(pre=icp.pre, eid="EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
    print(rpy.ked)

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()

    assert aid['name'] == "aid1"
    assert aid["salty"]["pidx"] == 0
    assert aid["prefix"] == icp.pre
    assert aid["salty"]["stem"] == "signify:aid"

    aid2 = identifiers.create("aid2", count=3, ncount=3, isith="2", nsith="2")
    icp2 = Serder(ked=aid2)
    assert icp2.pre == "EI5e4q43vsTsy-vJFcVGKfI3YKHbOT5ffuseaxtuYydL"
    assert len(icp2.verfers) == 3
    assert icp2.verfers[0].qb64 == "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
    assert icp2.verfers[1].qb64 == "DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"
    assert icp2.verfers[2].qb64 == "DEfdjYZMI2hLaHBOpUubn5AUItgOvh2W1vckGE33SIPf"
    assert len(icp2.digers) == 3
    assert icp2.digers[0].qb64 == "EEvyqpRLktts-_aSfPHKKv1mTKTV4ngwKKkOaqm3ZuPX"
    assert icp2.digers[1].qb64 == "EEkMimwsv_JMZh7k-Rfq5wvhvbEdjVr8NhGQpyssVmNJ"
    assert icp2.digers[2].qb64 == "EJy_MjjMWLJkn_5cRaUtDr7asfLe70xbAPD2nablr0iv"
    assert icp2.tholder.num == 2
    assert icp2.ntholder.num == 2

    aids = identifiers.list()
    assert len(aids) == 2
    aid = aids[1]
    assert aid['name'] == "aid2"
    assert aid["salty"]["pidx"] == 1
    assert aid["prefix"] == icp2.pre
    assert aid["salty"]["stem"] == "signify:aid"

    ked = identifiers.rotate("aid1")
    rot = Serder(ked=ked)

    assert rot.said == "EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg"
    assert rot.sn == 1
    assert len(rot.digers) == 1
    assert rot.digers[0].qb64 == "EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"

    ked = identifiers.interact("aid1", data=[icp.pre])
    ixn = Serder(ked=ked)
    assert ixn.said == "ENsmRAg_oM7Hl1S-GTRMA7s4y760lQMjzl0aqOQ2iTce"
    assert ixn.sn == 2
    assert ixn.ked["a"] == [icp.pre]


@responses.activate
def test_witnesses():
    responses._add_from_file(file_path=os.path.join(TEST_DIR, "witness.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect()
    assert client.agent is not None
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == "EJoqUMpQAfqsJhBqv02ehR-9BJYBTCrW8h5JlLdMTWBg"
    assert client.ctrl.ridx == 0

    identifiers = client.identifiers()
    operations = client.operations()

    # Use witnesses
    op = identifiers.create("aid1", toad="2", wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"])

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp1 = Serder(ked=op["response"])
    assert icp1.pre == "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"
    assert icp1.ked['b'] == ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                             "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                             "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
    assert icp1.ked['bt'] == "2"

    aid1 = identifiers.get("aid1")
    assert aid1["prefix"] == "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"
    assert len(aid1["windexes"]) == 3

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()
    assert aid['prefix'] == icp1.pre


@responses.activate
def test_delegation():
    responses._add_from_file(file_path=os.path.join(TEST_DIR, "delegation.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect()
    assert client.agent is not None
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    delpre = "EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7"
    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()

    op = oobis.resolve("http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness/"
                       "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha")

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    op = identifiers.create("aid1", toad="2", delpre=delpre, wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                                                   "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                                                   "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"])

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp1 = Serder(ked=op["response"])
    assert icp1.pre == "EITU8bCJwnaQSZn3aH6qIIud_9qh9Z8f0FlgLc6lqmGl"
