import pytest
import requests
import responses
from time import sleep

from .ecosystem import resetTestDirs, runWitnessDaemon, runKeriaDaemon

from keri import kering
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient

url = "http://localhost:3901"
bran = b'0123456789abcdefghijk'
tier = Tiers.low

agentPre = "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
ctrlPre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
grpPre = "ECQVcV-xHaJ-wyCrXnLo71aZYTidR1BElhXddadvC7m0"

host="localhost"
adminport=3901
httpport=3902
bootport=3903
burl = f"http://{host}:{bootport}/boot"
url = f"http://{host}:{adminport}"

states = [
    {'v': 'KERI10JSON0001b6_', 'i': 'EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3', 's': '0', 'p': '',
     'd': 'EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3', 'f': '0', 'dt': '2023-03-17T20:17:22.021742+00:00',
     'et': 'icp', 'kt': '1', 'k': ['DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I'], 'nt': '1',
     'n': ['EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N'], 'bt': '0', 'b': [], 'c': [],
     'ee': {'s': '0', 'd': 'EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3', 'br': [], 'ba': []}, 'di': ''},
    {'v': 'KERI10JSON0001b6_', 'i': 'EH0GZGSuPrwdqovzlEWjm3OMFCZ0GIMM8LUt70mSC3up', 's': '0', 'p': '',
     'd': 'EH0GZGSuPrwdqovzlEWjm3OMFCZ0GIMM8LUt70mSC3up', 'f': '0', 'dt': '2023-03-17T20:18:08.535887+00:00',
     'et': 'icp', 'kt': '1', 'k': ['DALBBwXiiUEgYcax8jKA6C1O7huSuoFsDJfxYfMLpaQC'], 'nt': '1',
     'n': ['ENyFbwVTyqa8prmA3KmmEvwl8KhSlcUhjWIgdXv_tcPj'], 'bt': '0', 'b': [], 'c': [],
     'ee': {'s': '0', 'd': 'EH0GZGSuPrwdqovzlEWjm3OMFCZ0GIMM8LUt70mSC3up', 'br': [], 'ba': []}, 'di': ''},
    {'v': 'KERI10JSON0001b6_', 'i': 'EHxb11g58Dam7nNDjqWD5U60v3oATS2hGbPh9WPtZhXu', 's': '0', 'p': '',
     'd': 'EHxb11g58Dam7nNDjqWD5U60v3oATS2hGbPh9WPtZhXu', 'f': '0', 'dt': '2023-03-17T20:18:28.749254+00:00',
     'et': 'icp', 'kt': '1', 'k': ['DDu97S0v2ofK2KUKOS1IqDeY7rBtppKtItAjB2nMF9gc'], 'nt': '1',
     'n': ['EJknp5MMpxG4s-IDjHKHYzc17loCUKtSsP6e1yDZrhx5'], 'bt': '0', 'b': [], 'c': [],
     'ee': {'s': '0', 'd': 'EHxb11g58Dam7nNDjqWD5U60v3oATS2hGbPh9WPtZhXu', 'br': [], 'ba': []}, 'di': ''}
]

@pytest.fixture
def setup():
    print("Before test", )
    resetTestDirs([ctrlPre,grpPre])
    
    # Start witness network
    all_procs = runWitnessDaemon()
    
    #start keria cloud agent
    all_procs = runKeriaDaemon()
    
    sleep(5)
    yield "setup"
    
    print("After test")
    for process in all_procs:
        print("Terminating processes {process}")
        process.terminate()
        print("Terminated processes {process}")

def test_incept(setup):
    print(f"Running {setup}")
    print(f"Running test_incept")
    
    client = SignifyClient(passcode=bran, tier=tier)
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

    groups = client.groups()
    assert groups is not None

    nstates = states

    # Test Defaults with states and nstates the same
    icp = groups.incept(states, nstates)

    assert icp.pre == "EAVMqJDVOXwaO3rbca1UdHwkkzahZi8JYQDViw6fkdeE"
    assert icp.ked["t"] == "icp"

    assert icp.ked["kt"] == "2"
    assert icp.ked['k'] == [
        "DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I",
        "DALBBwXiiUEgYcax8jKA6C1O7huSuoFsDJfxYfMLpaQC",
        "DDu97S0v2ofK2KUKOS1IqDeY7rBtppKtItAjB2nMF9gc"
    ]

    assert icp.ked["nt"] == "2"
    assert icp.ked['n'] == [
        "EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N",
        "ENyFbwVTyqa8prmA3KmmEvwl8KhSlcUhjWIgdXv_tcPj",
        "EJknp5MMpxG4s-IDjHKHYzc17loCUKtSsP6e1yDZrhx5"
    ]

    assert icp.ked["bt"] == "0"
    assert icp.ked["b"] == []
    assert icp.ked["a"] == []
    assert icp.ked["c"] == []

    # Test all other parameters
    icp = groups.incept(states, nstates, isith=["1/2", "1/2", "1/2"], nsith=["1/3", "1/3", "1/3"], toad="3",
                        wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                              "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                              "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX",
                              "BM35JN8XeJSEfpxopjn5jr7tAHCE5749f0OobhMLCorE"],
                        estOnly=True, DnD=True,
                        data=[dict(i="EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR", s=0,
                                   d="EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR")])

    assert icp.pre == grpPre
    assert icp.ked["t"] == "icp"

    assert icp.ked["kt"] == ["1/2", "1/2", "1/2"]
    assert icp.ked['k'] == [
        "DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I",
        "DALBBwXiiUEgYcax8jKA6C1O7huSuoFsDJfxYfMLpaQC",
        "DDu97S0v2ofK2KUKOS1IqDeY7rBtppKtItAjB2nMF9gc"
    ]

    assert icp.ked["nt"] == ["1/3", "1/3", "1/3"]
    assert icp.ked['n'] == [
        "EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N",
        "ENyFbwVTyqa8prmA3KmmEvwl8KhSlcUhjWIgdXv_tcPj",
        "EJknp5MMpxG4s-IDjHKHYzc17loCUKtSsP6e1yDZrhx5"
    ]

    assert icp.ked["bt"] == "3"
    assert icp.ked["b"] == ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX",
                            "BM35JN8XeJSEfpxopjn5jr7tAHCE5749f0OobhMLCorE"]
    assert icp.ked["a"] == [
        {
            "i": "EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR",
            "s": 0,
            "d": "EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR"
        }
    ]
    assert icp.ked["c"] == ["EO", "DND"]

    # Test delegation
    icp = groups.incept(states, nstates, delpre="EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR")
    assert icp.pre == "EG3BYTUJQ76D8mQdISRx76OTn3FWhIJgitFF9wJ6JTZr"
    assert icp.ked["t"] == "dip"
    assert icp.ked["di"] == "EImOExnAuY3_6C2J48HhGytUDAvQEB2Ypy6pLs0GxfBR"


def test_group_recipe(setup):
    print(f"Running {setup}")
    print(f"Running test_group_recipe")
    
    client = SignifyClient(passcode=bran, tier=tier)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    rsp1 = responses.Response(
        method="GET",
        url="http://localhost:3901/boot",
        json={"kel": [{"ked": {"v": "KERI10JSON000159_", "t": "icp",
                               "d": "EIDJUg2eR8YGZssffpuqQyiXcRVz2_Gw_fcAVWpUMie1",
                               "i": "EIDJUg2eR8YGZssffpuqQyiXcRVz2_Gw_fcAVWpUMie1", "s": "0", "kt": "1",
                               "k": ["DF_pwiZQiNWtvksHhOtoAYM6j3WTdzBmMQainmlbxSdT"], "nt": "1",
                               "n": ["EAksAMJTf2Cd1JYUq7fWy22hdPUFijBgrej4Wtfx2NFM"], "bt": "0", "b": [], "c": [],
                               "a": ["ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"]},
                       "sig":
                           "AAA8XCnIKkWfpgayz6GRfVPH_Fe4P55XF75fzY3iLT5YQsBiofNBWJI9OkiYro98b3Qrh85DDTW52cZ5fj2yz3gF"}],
              "pidx": 0}
    )
    responses.add(rsp1)
    rsp2 = responses.Response(
        method="POST",
        url="http://localhost:3901/boot",
        status=202
    )
    responses.add(rsp2)
    
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
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    assert client.agent.pre == agentPre

    groups = client.groups()
    assert groups is not None
    keyStates = client.keyStates()
    assert keyStates is not None

    responses.add(responses.Response(
        method="GET",
        url=f"http://localhost:3901/states?pre={agentPre}&"
            "pre=EG3BYTUJQ76D8mQdISRx76OTn3FWhIJgitFF9wJ6JTZr&pre=ECQVcV-xHaJ-wyCrXnLo71aZYTidR1BElhXddadvC7m0",
        json=states
    ))

    sts = keyStates.list(pres=[agentPre,
                               "EG3BYTUJQ76D8mQdISRx76OTn3FWhIJgitFF9wJ6JTZr",
                               "ECQVcV-xHaJ-wyCrXnLo71aZYTidR1BElhXddadvC7m0"])
    assert len(sts) == 1
    assert len(states) == 3

    nstates = states
    # Test all other parameters
    icp = groups.incept(states, nstates, isith=["1/2", "1/2", "1/2"], nsith=["1/3", "1/3", "1/3"])

    assert icp.pre == "EIKVdH89EFGZghyxZVNf-WxE6EpANuPLMTTBVYbUxbBG"
    assert icp.ked["t"] == "icp"

    assert icp.ked["kt"] == ["1/2", "1/2", "1/2"]
    assert icp.ked['k'] == [
        "DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I",
        "DALBBwXiiUEgYcax8jKA6C1O7huSuoFsDJfxYfMLpaQC",
        "DDu97S0v2ofK2KUKOS1IqDeY7rBtppKtItAjB2nMF9gc"
    ]

    assert icp.ked["nt"] == ["1/3", "1/3", "1/3"]
    assert icp.ked['n'] == [
        "EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N",
        "ENyFbwVTyqa8prmA3KmmEvwl8KhSlcUhjWIgdXv_tcPj",
        "EJknp5MMpxG4s-IDjHKHYzc17loCUKtSsP6e1yDZrhx5"
    ]