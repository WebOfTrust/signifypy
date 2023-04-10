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
        SignifyClient(url=url, bran=bran[:16], tier=tier)

    # Try with an invalid URL
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(url="ftp://www.example.com", bran=bran, tier=tier)

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELvxjlGm4zGdItzUa6Mg0ZP_gvvbisl7N5DUceKdOqGj"

    tier = Tiers.low
    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELvxjlGm4zGdItzUa6Mg0ZP_gvvbisl7N5DUceKdOqGj"

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    tier = Tiers.med
    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"

    tier = Tiers.high
    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "EB8wN2c_tv1WlsJ5c3949-TFWPMB2IflFbdMlZfC_Hgo"


@responses.activate
def test_connect():
    responses._add_from_file(file_path=os.path.join(TEST_DIR, "connect.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELvxjlGm4zGdItzUa6Mg0ZP_gvvbisl7N5DUceKdOqGj"

    # Raises configuration error because the started agent has a different controller AID
    with pytest.raises(kering.ConfigurationError):
        client.connect()

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect()
    assert client.agent is not None
    assert client.agent.anchor == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == "EIDJUg2eR8YGZssffpuqQyiXcRVz2_Gw_fcAVWpUMie1"
    assert client.ctrl.ridx == 0

    identifiers = client.identifiers()
    aids = identifiers.list()
    assert aids == []

    aid = identifiers.create("aid1")
    icp = Serder(ked=aid)
    assert icp.pre == "ED6GSHpz7zeEBYwkBYT3SZFjAGTP3iLt_SMa2-hznjLQ"
    assert len(icp.verfers) == 1
    assert icp.verfers[0].qb64 == "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
    assert len(icp.digers) == 1
    assert icp.digers[0].qb64 == "ENIJ_qTj6Zb6GgSCvLPUPaf7ypO0KfyxBfJcmwrioCdr"
    assert icp.tholder.num == 1
    assert icp.ntholder.num == 1

    rpy = identifiers.makeEndRole(pre=icp.pre, eid="EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
    print(rpy.ked)

    aids = identifiers.list()
    assert len(aids) == 1
    aid = aids.pop()

    assert aid['name'] == "aid1"
    assert aid["pidx"] == 0
    assert aid["prefix"] == icp.pre
    assert aid["stem"] == "signify:aid"

    aid2 = identifiers.create("aid2", count=3, ncount=3, isith="2", nsith="2")
    icp2 = Serder(ked=aid2)
    assert icp2.pre == "EIcPqJrvwYirK5ABfOcDEP3NEYOEX5LUr8NnLrbWeMpU"
    assert len(icp2.verfers) == 3
    assert icp2.verfers[0].qb64 == "DMT7Xy_FUitLxWX0tHgsOOhW50iloHbXjlF_xaXCCxwv"
    assert icp2.verfers[1].qb64 == "DBtqxaApH5G2jmlnuUeckKc6ntieS41vmR9E1K93WyNd"
    assert icp2.verfers[2].qb64 == "DM750nt2-lKzCLIIJqzh61SILLz-nrEgkczcLH9m9GT6"
    assert len(icp2.digers) == 3
    assert icp2.digers[0].qb64 == "ECkMSLcBB8UNzhIrjFBXFP11nLB_4CaJv_18ew5McpP6"
    assert icp2.digers[1].qb64 == "EDxKP6QLbAJQtoOHAPMVxYI-7I6oB8fCgRcjNmxSTXFC"
    assert icp2.digers[2].qb64 == "EEScGcKIiH3uv4oHnrcZzTHwXW5h6AexqQhh52PUz4fB"
    assert icp2.tholder.num == 2
    assert icp2.ntholder.num == 2

    aids = identifiers.list()
    assert len(aids) == 2
    aid = aids[1]
    assert aid['name'] == "aid2"
    assert aid["pidx"] == 1
    assert aid["prefix"] == icp2.pre
    assert aid["stem"] == "signify:aid"

    ked = identifiers.rotate("aid1")
    rot = Serder(ked=ked)

    assert rot.said == "EKzEsFo3CWCFdKPb1L33iHqm7smqRIy9IlMaa1uH5ZJk"
    assert rot.sn == 1
    assert len(rot.digers) == 1
    assert rot.digers[0].qb64 == "EIQVCPiXmmpLtbSBt0CyKVscky56BUEATKrc2qC7FIYA"

    ked = identifiers.interact("aid1", data=[icp.pre])
    ixn = Serder(ked=ked)
    assert ixn.said == "EJyW-3Bfrr9jMkjc1hRUmGclCnAWpNqFbLy5QtH9qvAy"
    assert ixn.sn == 2
    assert ixn.ked["a"] == [icp.pre]


@responses.activate
def test_witnesses():
    responses._add_from_file(file_path=os.path.join(TEST_DIR, "witness.toml"))
    url = "http://localhost:3901"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect()
    assert client.agent is not None
    assert client.agent.anchor == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == "EFebpJik0emPaSuvoSPYuLVpSAsaWVDwf4WYVPOBva_p"
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
    assert icp1.pre == "EALbxdf4Voh2LFEEQlCWYe3pxiEK3efIZ88VQwz2Q1nO"
    assert icp1.ked['b'] == ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                             "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                             "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
    assert icp1.ked['bt'] == "2"

    aid1 = identifiers.get("aid1")
    assert aid1["prefix"] == "EALbxdf4Voh2LFEEQlCWYe3pxiEK3efIZ88VQwz2Q1nO"
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

    client = SignifyClient(url=url, bran=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    client.connect()
    assert client.agent is not None
    assert client.agent.anchor == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

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
