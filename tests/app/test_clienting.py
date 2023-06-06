# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import os
from time import sleep
import requests
import responses

import pytest
from keri import kering
from keri.app.keeping import Algos
from keri.core.coring import Tiers, Serder

from keria.app.cli.commands import start
from keria.testing.testing_helper import Helpers

from signify.app.clienting import SignifyClient

import threading

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


bran = '0123456789abcdefghijk'
ctrlPre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
agentPre = "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
kName = "keria"
url = "http://localhost:3901"

class KeriaArgs: 
    def __init__(self):
        self.name="keria"
        self.base="testing"
        self.bran = bran
        self.admin="3901"
        self.http="3902"
        self.boot="3903"
        self.configFile="demo-witness-oobis.json"
        self.configDir="/Users/meenyleeny/VSCode/keria/scripts"


@pytest.fixture
def setup():
    print("Before test", )
    Helpers.remove_test_dirs(ctrlPre)
    thread=threading.Thread(target=start.runAgent,
                     args=[kName,
                    "",
                    bran,
                    3901,
                    3902,
                    3903,
                    "demo-witness-oobis.json",
                    "/Users/meenyleeny/VSCode/keria/scripts",
                    0.0])
    thread.daemon=True
    thread.start()

@pytest.fixture
def teardown():
    print("After test")
    
def test_init(setup,teardown):
    tier = None
    
    # Try with bran that is too short
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url=url, passcode=bran[:16], tier=tier)

    # Try with an invalid URL
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url="ftp://www.example.com", passcode=bran, tier=tier)

    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == ctrlPre

    tier = Tiers.low
    client = SignifyClient(url=url, passcode=bran, tier=tier)
    assert client.controller == ctrlPre

    # Raises configuration error because the started agent has a different controller AID
    # assert client.controller == "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"
    with pytest.raises(kering.ConfigurationError):
        tier = Tiers.med
        client = SignifyClient(url=url, passcode=bran, tier=tier)

    # assert client.controller == "EB8wN2c_tv1WlsJ5c3949-TFWPMB2IflFbdMlZfC_Hgo"
    with pytest.raises(kering.ConfigurationError):
        tier = Tiers.high
        client = SignifyClient(url=url, passcode=bran, tier=tier)

# def request_callback(request):
#     headers = {"SIGNIFY-RESOURCE": "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei",
#             "SIGNIFY-TIMESTAMP": "2022-09-24T00:05:48.196795+00:00",
#             'SIGNATURE-INPUT': 'signify=("@method" "@path" "content-length" '
#                                                     '"signify-resource" '
#                                                     '"signify-timestamp");created=1609459200;keyid="EJ-t3M9T3Sq0Xa6XmpWMoNtstEqJWvJoXD_GdIRwvINc";alg="ed25519"',
#             "SIGNATURE": 'indexed="?0";signify="0BAagZpIHOhyE98pffMUXpqQPVmpTjvVyAE1DFWsqEPLVbE4fQaR7B3DTcwoYKFs0k9A4OFQh6C0bATNfVs5wLwH"'
#             }
#     return (200, headers, request.body)

# @responses.activate
def test_connect(setup,teardown):
    # url = "http://localhost:3901"
    # responses._add_from_file(file_path=os.path.join(TEST_DIR, "connect.toml"))
    #responses.add_callback(content_type="text/plain",method="GET",url="http://localhost:3901/identifiers?last=&limit=25",callback=request_callback)
    #bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == ctrlPre

    evt, siger = client.ctrl.event()

    print(evt.pretty())
    print(siger.qb64)
    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    client.connect(url=url)
    assert client.agent is not None
    assert client.agent.pre == agentPre
    assert client.agent.delpre == ctrlPre

    identifiers = client.identifiers()
    aids = identifiers.list()
    assert aids == []

    aid = identifiers.create("aid1", bran=f"{bran}_1")
    icp = Serder(ked=aid)
    assert icp.pre == "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"
    assert len(icp.verfers) == 1
    assert icp.verfers[0].qb64 == "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
    assert len(icp.digers) == 1
    assert icp.digers[0].qb64 == "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"
    assert icp.tholder.num == 1
    assert icp.ntholder.num == 1

    rpy = identifiers.makeEndRole(pre=icp.pre, eid="EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
    print(rpy.pretty())
    assert rpy.ked['a']['cid'] == "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"
    assert rpy.ked['a']['eid'] == "EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf"

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()

    salt = aid[Algos.salty]
    assert aid['name'] == "aid1"
    assert salt["pidx"] == 0
    assert aid["prefix"] == icp.pre
    assert salt["stem"] == "signify:aid"

    aid2 = identifiers.create("aid2", count=3, ncount=3, isith="2", nsith="2", bran="0123456789lmnopqrstuv")
    icp2 = Serder(ked=aid2)
    print(icp2.pre)
    assert icp2.pre == "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX"
    assert len(icp2.verfers) == 3
    assert icp2.verfers[0].qb64 == "DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5"
    assert icp2.verfers[1].qb64 == "DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz"
    assert icp2.verfers[2].qb64 == "DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze"
    assert len(icp2.digers) == 3
    print([diger.qb64 for diger in icp2.digers])
    assert icp2.digers[0].qb64 == "EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH"
    assert icp2.digers[1].qb64 == "EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg"
    assert icp2.digers[2].qb64 == "ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60"
    assert icp2.tholder.num == 2
    assert icp2.ntholder.num == 2

    aids = identifiers.list()
    assert len(aids) == 2
    aid = aids[1]
    assert aid['name'] == "aid2"
    assert aid["prefix"] == icp2.pre
    salt = aid[Algos.salty]
    assert salt["pidx"] == 1
    assert salt["stem"] == "signify:aid"

    ked = identifiers.rotate("aid1")
    rot = Serder(ked=ked)

    assert rot.said == "EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg"
    assert rot.sn == 1
    assert len(rot.digers) == 1
    assert rot.verfers[0].qb64 == "DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"
    assert rot.digers[0].qb64 == "EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"

    ked = identifiers.interact("aid1", data=[icp.pre])
    ixn = Serder(ked=ked)
    assert ixn.said == "ENsmRAg_oM7Hl1S-GTRMA7s4y760lQMjzl0aqOQ2iTce"
    assert ixn.sn == 2
    assert ixn.ked["a"] == [icp.pre]

    aid = identifiers.get("aid1")
    state = aid["state"]
    assert state['s'] == '2'
    assert state['f'] == '2'
    assert state['et'] == 'ixn'
    assert state['d'] == ixn.said
    assert state['ee']['d'] == rot.said

    events = client.keyEvents()
    log = events.get(pre=aid["prefix"])
    assert len(log) == 3
    serder = Serder(ked=log[0])
    assert serder.pre == icp.pre
    assert serder.said == icp.said
    serder = Serder(ked=log[1])
    assert serder.pre == rot.pre
    assert serder.said == rot.said
    serder = Serder(ked=log[2])
    assert serder.pre == ixn.pre
    assert serder.said == ixn.said

    print(identifiers.list())

# @responses.activate
def test_witnesses(setup,teardown):
    # responses._add_from_file(file_path=os.path.join(TEST_DIR, "witness.toml"))
    # url = "http://localhost:3901"
    # bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    evt, siger = client.ctrl.event()
    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))
    
    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")
    
    client.connect(url=url)
    assert client.agent is not None
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"

    identifiers = client.identifiers()
    operations = client.operations()

    # Use witnesses
    op = identifiers.create("aid1", bran="canIGetAWitnessSaltGreaterThan21", toad="2", wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"])

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp1 = Serder(ked=op["response"])
    assert icp1.pre == "EGTFIbnFoA7G-f4FHzzXUMp6VAgQfJ-2nXqzfb5hVwKa"
    assert icp1.ked['b'] == ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                             "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                             "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
    assert icp1.ked['bt'] == "2"

    aid1 = identifiers.get("aid1")
    assert aid1["prefix"] == icp1.pre
    assert len(aid1["windexes"]) == 3

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()
    assert aid['prefix'] == icp1.pre


@responses.activate
def test_delegation():
    # responses._add_from_file(file_path=os.path.join(TEST_DIR, "delegation.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect(url=url)
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
