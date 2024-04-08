# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_authing module

Testing authing with unit tests
"""

from keri import kering
from keri.core import serdering
from keri.core.coring import Tiers
from keri.kering import Serials, versify
from mockito import mock, unstub, expect, verifyNoUnwantedInteractions
import pytest


def rt(a, b, c):
    return True


def test_verify():
    agent = mock({'pre': "EEz01234"})
    ctrl = mock()

    from signify.core.authing import Authenticater
    authn = Authenticater(agent, ctrl)

    import requests
    mock_request = mock({'method': 'GET', 'url': 'http://example.com/my_path', 'headers': {}, 'body': "a body for len"},
                        spec=requests.Request, strict=True)
    mock_rep = mock({'request': mock_request, 'headers': {}}, spec=requests.Response, strict=True)

    with pytest.raises(kering.AuthNError):
        authn.verify(rep=mock_rep)

    mock_rep = mock({'request': mock_request, 'headers': {"SIGNIFY-RESOURCE": 'EABC'}}, spec=requests.Response,
                    strict=True)

    with pytest.raises(kering.AuthNError):
        authn.verify(rep=mock_rep)

    # Swap out verifysig so we can test verify
    authn.verifysig = rt
    mock_rep = mock({'request': mock_request, 'headers': {"SIGNIFY-RESOURCE": 'EEz01234'}}, spec=requests.Response,
                    strict=True)

    authn.verify(rep=mock_rep)
    verifyNoUnwantedInteractions()
    unstub()


def test_agent(): 
    mock_verfer = mock()
    from keri.core import coring
    expect(coring, times=1).Verfer(qb64="key").thenReturn(mock_verfer)

    keys = ['key']
    state = {
        'i': 'pre',
        's': 0,
        'di': 'delpre',
        'd': 'said',
        'k': keys,
    }
    from signify.core.authing import Agent
    agent = Agent(state=state)

    assert agent.pre == "pre"
    assert agent.delpre == "delpre"
    assert agent.said == "said"
    assert agent.sn == 0
    assert agent.verfer == mock_verfer

    verifyNoUnwantedInteractions()
    unstub()

    from keri import kering
    with pytest.raises(kering.ValidationError):
        keys.append("another key")
        state['k'] = keys
        agent = Agent(state=state)


@pytest.mark.parametrize('bran', [
    ("abcdefghijklmnop01234"),
    (b"abcdefghijklmnop01234"),
])
def test_controller(bran):
    from signify.core.authing import Controller
    from keri.core.coring import Tiers
    ctrl = Controller(bran=bran, tier=Tiers.low)

    assert ctrl.bran == "0AAabcdefghijklmnop01234"
    assert ctrl.stem == "signify:controller"

    assert ctrl.tier == Tiers.low

    from keri.core import coring
    assert type(ctrl.salter) is coring.Salter
    assert type(ctrl.signer) is coring.Signer
    assert ctrl.signer.code == "A"
    assert ctrl.signer.qb64 == "AF1iHYsl-7DZFD71kcsg5iUAkLP3Lh_01RZFEHhL3629"

    assert type(ctrl.nsigner) is coring.Signer
    assert ctrl.nsigner.code == "A"
    assert ctrl.nsigner.qb64 == "AGG0prnUWeKJGfh00-rrSqBIxR0Mx5K1FP0XC_UtCdjX"

    assert ctrl.keys == ["DEps8kAE90Ab9Fs_MLaES9Pre-ba3eOZCY2H7HIENVug"]
    assert ctrl.ndigs == ["EAioAm-C0hG3oG4NplWhh7Uc43C2cpkbLX2Bj5yIKkna"]

    raw = b'{"v":"KERI10JSON00012b_","t":"icp","d":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","i":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","s":"0","kt":"1","k":["DEps8kAE90Ab9Fs_MLaES9Pre-ba3eOZCY2H7HIENVug"],"nt":"1","n":["EAioAm-C0hG3oG4NplWhh7Uc43C2cpkbLX2Bj5yIKkna"],"bt":"0","b":[],"c":[],"a":[]}'
    assert ctrl.serder.raw == raw
    assert ctrl.pre == "EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV"

    # self serder
    assert ctrl.event()[0].raw == raw
    # self.signer.sign
    assert ctrl.event()[1].raw == (b'\x8a\xf6\x7f\x9e\xc8%\xc4\xe9\xc1<p\x8as\xd3[\x95k;\xe1\xe1\xce\x84\xcf\xe3'
                                   b'\t\xf9\x7f}\xeeb\xa6c\xe21-t\x17h\xad\x91\x14\xf7\x88L\xdc5\xaf\xc6'
                                   b'\x05\xc0\x01\xd3\x9f}\xbf\xe7\x06\x80\xfb\x80\x14*\x8c\x04')


def test_controller_derive():
    from signify.core.authing import Controller
    from keri.core.coring import Tiers
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)
    serder = ctrl.derive(state=None)
    raw = b'{"v":"KERI10JSON00012b_","t":"icp","d":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","i":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","s":"0","kt":"1","k":["DEps8kAE90Ab9Fs_MLaES9Pre-ba3eOZCY2H7HIENVug"],"nt":"1","n":["EAioAm-C0hG3oG4NplWhh7Uc43C2cpkbLX2Bj5yIKkna"],"bt":"0","b":[],"c":[],"a":[]}'
    assert serder.raw == raw

    serder = ctrl.derive(state={"ee": {"s": "0"}})
    assert serder.raw == raw

    from keri.core import coring
    e1 = dict(v=versify(kind=Serials.json, size=0),
              t="rot",
              d="",
              i="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV",
              s="1",
              p="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV",
              kt="1",
              k=["DMZy6qbgnKzvCE594tQ4SPs6pIECXTYQBH7BkC4hNY3E"],
              nt="1",
              n=["EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV"],
              bt="0",
              br=[],
              ba=[],
              a=[]
              )
    
    _, e1 = coring.Saider.saidify(sad=e1)

    from signify.signifying import State
    state = State(controller={"ee": e1})
    serder = ctrl.derive(state=state)

    assert serder.raw == (b'{"v":"KERI10JSON000160_","t":"rot","d":"ENvjVqUoq2SGDrFSzqI5AI37ZE4IAlKLdFGw'
                          b'Uzf7Ir7I","i":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","s":"1","p":"EM'
                          b'PYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","kt":"1","k":["DMZy6qbgnKzvCE594'
                          b'tQ4SPs6pIECXTYQBH7BkC4hNY3E"],"nt":"1","n":["EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8'
                          b'A3jjXxqYawLcV"],"bt":"0","br":[],"ba":[],"a":[]}')


def test_approve_delegation():
    from signify.core.authing import Controller
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

    mock_agent = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,
    })

    from keri.core import coring
    e1 = dict(v="KERI10JSON000000_",
              d="",
              i="ABCDEFG",
              s="1",
              t="int")
    _, e1 = coring.Saider.saidify(sad=e1)

    from keri.core import eventing
    expect(eventing, times=1).interact(
        pre="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        dig="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        sn=1,
        data=[{'i': 'pre', 's': '1', 'd': 'said'}]).thenReturn(serdering.SerderKERI(sad=e1))

    serder, sig = ctrl.approveDelegation(agent=mock_agent)
    
    assert serder.raw == b'{"v":"KERI10JSON00006c_","d":"EAnymWG0hPrDWRxKNyYxuHqZle6sT5y_QlW8pf_SfyOu","i":"ABCDEFG","s":"1","t":"int"}'
    assert sig[0] == "AAD3uTIT98auX5wgbXxq7PnO95vyxMAJ-JWd_PalgDWRyhzkg-0B_hHPh3TAP8dknnwMcBnRjwIDD87YLQOmLL0P"

    verifyNoUnwantedInteractions()
    unstub()


def test_approve_delegation(): 
    from signify.core.authing import Controller
    from keri.core.coring import Tiers
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

    from signify.core.authing import Agent
    mock_agent = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,
    }, spec=Agent, strict=True)

    from keri.core.serdering import Serder
    mock_serder = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,  
        'raw': b'',
    }, spec=Serder, strict=True)

    from keri.core import eventing
    expect(eventing, times=1).interact(
        pre="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        dig="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        sn=1,
        data=[{'i': 'pre', 's': '1', 'd': 'said'}]).thenReturn(mock_serder)
    
    mock_signature = mock(
        {'qb64': 'AADi_WkHWZZZsJSm78xV8GqnXDM7roNGvOPpYzwm3eYAHjrOvhCUXyyd8_pHDzZxXG1ESOpzKQmbgx3_MYxBno4M'}
    )
    expect(ctrl.signer, times=1).sign(mock_serder.raw, index=0).thenReturn(mock_signature)

    serder, sig = ctrl.approveDelegation(agent=mock_agent)
    
    assert ctrl.serder == mock_serder
    assert serder == mock_serder
    assert sig[0] == mock_signature.qb64

    verifyNoUnwantedInteractions()
    unstub()


def test_controller_rotate_salty():
    from signify.core.authing import Controller
    from keri.core.coring import Tiers
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)    

    aid_one = {
               "name": "aid1", 
               "prefix": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", 
               "salty": {
                   "pidx": 0, 
                   "stem":"signify:aid", 
                   "sxlt": "1AAH2R_SPhr_5vIBGGtyVamaGVDQAcYlgmwDOkJwM-q6Qw8K5NT7jLzJ0k6_7sa3oyKK33ym8JX1Il4MoUiy8ixYwsVWYhaU3sMT",
                   "tier": "low",
                   "icodes": ["A"],
                   "kidx": 0,
                   "transferable": False,
                },
                "state": {
                    "k": ["BAzUCcD85Cs62fLeBEk6ewziVohx2kXnzuANqspIcwS2"],
                },
            }
    out = ctrl.rotate(nbran="0123456789abcdefghijk", aids=[aid_one],)

    assert 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK' in out['keys']
    assert 'sxlt' in out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'] # type: ignore
    assert out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK']['sxlt'] != "1AAH2R_SPhr_5vIBGGtyVamaGVDQAcYlgmwDOkJwM-q6Qw8K5NT7jLzJ0k6_7sa3oyKK33ym8JX1Il4MoUiy8ixYwsVWYhaU3sMT" # type: ignore

# def test_controller_rotate_randy():
#     from keri.core.coring import Tiers
#     from signify.core.authing import Controller
#     ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

#     from keri.core.coring import Salter
#     mock_salter = mock({'qb64': 'salter qb64'}, spec=Salter, strict=True)
#     ctrl.salter = mock_salter

#     from signify.core.keeping import SaltyCreator
#     mock_creator = mock({'create': lambda ridx, tier : None}, spec=SaltyCreator, strict=True)
#     from signify.core import keeping
#     when(keeping).SaltyCreator(salt='salter qb64', stem='signify:controller', tier=Tiers.low).thenReturn(mock_creator)

#     from keri.core.coring import Signer
#     mock_signer = mock(spec=Signer, strict=True)
#     ctrl.signer = mock_signer
#     mock_nsigner = mock(spec=Signer, strict=True)
#     ctrl.nsigner = mock_nsigner
#     ctrl.keys = ['a key']
#     from keri.core.coring import Diger
#     mock_diger = mock(spec=Diger, strict=True)
#     ctrl.ndigs = [mock_diger]

#     from keri.core.serdering import Serder
#     mock_serder = mock(spec=Serder, strict=True)
#     ctrl.serder = mock_serder

#     # end controller mock setup
#     assert ctrl.bran == '0AAabcdefghijklmnop01234'

#     # mocks for rotate
#     when(mock_salter).signer(transferable=False).thenReturn(mock_nsigner)
#     mock_nsalter = mock(spec=Salter, strict=True)
#     from keri.core import coring
#     when(coring).Salter(qb64='0AA0123456789abcdefghijk').thenReturn(mock_nsalter)

    # from signify.core.keeping import SaltyCreator
    # mock_ncreator = mock(spec=SaltyCreator, strict=True)

    # from signify.core import keeping
    # expect(keeping, times=1).SaltyCreator(salt='salter qb64', stem='signify:controller', tier=Tiers.low).thenReturn(mock_ncreator)

    # ctrl.rotate(nbran="0123456789abcdefghijk", aids=["aid_one"],) 