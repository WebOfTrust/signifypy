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
from keri.app.cli.commands.witness import start as wstart
from keri.app.keeping import Algos
from keri.core.coring import Tiers, Serder

from keria.app.cli.commands import start as kstart
from keria.testing.testing_helper import Helpers

from signify.app.clienting import SignifyClient

import threading

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

host="localhost"
adminport=3901
httpport=3902
bootport=3903
agentPre = "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
ctrlPre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
base=""
kname="keria"
kbran=""
wname="witness"
wbase=""
walias="witness"
wbran=""
wtcp=5631
whttp=5632
wexpire=0.0
bran = "0123456789abcdefghijk"
burl = f"http://{host}:{bootport}/boot"
url = f"http://{host}:{adminport}"
configDir=f"{cwd}/tests/"
configFile="demo-witness-oobis.json"
wconfigDir=f"{cwd}/tests/"
wconfigFile="demo-witness-oobis.json"
wit1 = "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"
wit2 = "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM"
wit3 = "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"

@pytest.fixture
def setup():
    print("Before test", )
    Helpers.remove_test_dirs(ctrlPre)
    
    # Start witness network
    wThread=threading.Thread(target=wstart.runWitness,
                             args=[wname,
               wbase,
               walias,
               wbran,
               wtcp,
               whttp,
               wconfigDir,
               wconfigFile])
    wThread.daemon=True
    wThread.start()
    
    # Start keria cloud agent
    kThread=threading.Thread(target=kstart.runAgent,
                     args=[kname,
                    base,
                    kbran,
                    adminport,
                    httpport,
                    bootport,
                    configFile,
                    configDir,
                    0.0])
    kThread.daemon=True
    kThread.start()

@pytest.fixture
def teardown():
    print("After test")
    
def test_init(setup,teardown):
    # Try with bran that is too short
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(passcode=bran[:16], tier=Tiers.low)

    # Try with an invalid URL
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url="ftp://www.example.com", passcode=bran, tier=Tiers.low)

    client = SignifyClient(passcode=bran)
    assert client.controller == ctrlPre

    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == ctrlPre

    tier = Tiers.med
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller != ctrlPre

    tier = Tiers.high
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller != ctrlPre

def test_connect(setup,teardown):
    client = SignifyClient(passcode=bran, tier=Tiers.low)
    assert client.controller == ctrlPre

    evt, siger = client.ctrl.event()

    print(evt.pretty())
    print(siger.qb64)
    res = requests.post(url=burl,
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

    op1 = identifiers.create("aid1", bran=f"{bran}_1")
    aid = op1["response"]
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

    op2 = identifiers.create("aid2", count=3, ncount=3, isith="2", nsith="2", bran="0123456789lmnopqrstuv")
    aid2 = op2["response"]
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

    op3 = identifiers.rotate("aid1")
    ked = op3["response"]
    rot = Serder(ked=ked)

    assert rot.said == "EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg"
    assert rot.sn == 1
    assert len(rot.digers) == 1
    assert rot.verfers[0].qb64 == "DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"
    assert rot.digers[0].qb64 == "EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"

    op4 = identifiers.interact("aid1", data=[icp.pre])
    ked = op4["response"]
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

def test_witnesses(setup,teardown):
    client = SignifyClient(passcode=bran, tier=Tiers.low)
    assert client.controller == ctrlPre
    evt, siger = client.ctrl.event()
    res = requests.post(url=burl,
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
    assert client.agent.delpre == ctrlPre
    assert client.agent.pre == agentPre

    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()

    op = oobis.resolve(f"http://127.0.0.1:5642/oobi/{agentPre}/witness")
    print("OOBI op is: ", op)
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    # op = oobis.resolve(f"http://127.0.0.1:5642/oobi/{agentPre}/witness")

    # Use witnesses
    op = identifiers.create("aid1", bran="canIGetAWitnessSaltGreaterThan21", toad="2", 
                            wits=[wit1, wit2, wit3])

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp1 = Serder(ked=op["response"])
    assert icp1.pre == "EGTFIbnFoA7G-f4FHzzXUMp6VAgQfJ-2nXqzfb5hVwKa"
    assert icp1.ked['b'] == [wit1,
                             wit2,
                             wit3]
    assert icp1.ked['bt'] == "2"

    aid1 = identifiers.get("aid1")
    assert aid1["prefix"] == icp1.pre
    assert len(aid1["windexes"]) == 3

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()
    assert aid['prefix'] == icp1.pre


def test_delegation(setup,teardown):
    client = SignifyClient(passcode=bran, tier=Tiers.low)
    print(client.controller)
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

    # Delegator OOBI:
    # http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness

    delpre = "EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7"
    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()

    op = oobis.resolve(f"http://127.0.0.1:5642/oobi/{delpre}/witness")
    print("OOBI op is: ", op)

    count = 0
    while not op["done"] and not count > 25:
        op = operations.get(op["name"])
        sleep(1)

    op = identifiers.create("aid1", toad="2", delpre=delpre, wits=[wit1, wit2, wit3])
    pre = op["metadata"]["pre"]

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp1 = Serder(ked=op["response"])

    print(icp1.pretty())
    assert icp1.pre == pre
