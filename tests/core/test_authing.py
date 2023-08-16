
from keri import kering
from keri.core.coring import Tiers
from mockito import mock, unstub, when
import pytest
from signify.app.clienting import State
from signify.core.authing import Agent, Controller

def test_agent(): 
    mock_verfer = mock()
    from keri.core import coring
    when(coring).Verfer(qb64="key").thenReturn(mock_verfer)

    keys = ['key']
    state = {
        'i': 'pre',
        's': 0,
        'di': 'delpre',
        'd': 'said',
        'k': keys,
    }
    agent = Agent(state=state)

    assert agent.pre == "pre"
    assert agent.delpre == "delpre"
    assert agent.said == "said"
    assert agent.sn == 0
    assert agent.verfer == mock_verfer

    unstub()

    with pytest.raises(kering.ValidationError):
        keys.append("another key")
        state['k'] = keys
        agent = Agent(state=state)


def test_controller():
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

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
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)
    serder = ctrl.derive(state=None)
    raw = b'{"v":"KERI10JSON00012b_","t":"icp","d":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","i":"EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV","s":"0","kt":"1","k":["DEps8kAE90Ab9Fs_MLaES9Pre-ba3eOZCY2H7HIENVug"],"nt":"1","n":["EAioAm-C0hG3oG4NplWhh7Uc43C2cpkbLX2Bj5yIKkna"],"bt":"0","b":[],"c":[],"a":[]}'
    assert serder.raw == raw

    serder = ctrl.derive(state={"ee": {"s": "0"}})
    assert serder.raw == raw

    from keri.core import coring
    e1 = dict(v=coring.Vstrings.json,
              d="",
              i="ABCDEFG",
              s="0001",
              t="rot")
    
    _, e1 = coring.Saider.saidify(sad=e1)
    state = State(controller={"ee": e1})
    serder = ctrl.derive(state=state)

    assert serder.raw == (b'{"v":"KERI10JSON00006f_","d":"EIM66TjBMfwPnbwK7oZqbZyGz9nOeVmQHeH3NZxrsk8F",'
                          b'"i":"ABCDEFG","s":"0001","t":"rot"}')

def test_approve_delegation():
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

    mock_agent = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,
    })

    from keri.core import coring
    e1 = dict(v=coring.Vstrings.json,
              d="",
              i="ABCDEFG",
              s="1",
              t="int")
    _, e1 = coring.Saider.saidify(sad=e1)

    from keri.core import eventing
    when(eventing).interact(
        pre="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        dig="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        sn=1,
        data=[{'i': 'pre', 's': '1', 'd': 'said'}]).thenReturn(coring.Serder(ked=e1))

    serder, sig = ctrl.approveDelegation(agent=mock_agent)
    
    assert serder.raw == b'{"v":"KERI10JSON00006c_","d":"EAnymWG0hPrDWRxKNyYxuHqZle6sT5y_QlW8pf_SfyOu","i":"ABCDEFG","s":"1","t":"int"}'
    assert sig[0] == "AAD3uTIT98auX5wgbXxq7PnO95vyxMAJ-JWd_PalgDWRyhzkg-0B_hHPh3TAP8dknnwMcBnRjwIDD87YLQOmLL0P"

    unstub()

def test_approve_delegation_pure_mock(): 
    ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

    mock_agent = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,
    })

    mock_serder = mock({
        'said': 'said',
        'pre': 'pre',
        'sn': 1,  
        'raw': b'',
    })

    from keri.core import eventing
    when(eventing).interact(
        pre="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        dig="EMPYj-h2OoCyPGQoUUd1tLUYe62YD_8A3jjXxqYawLcV", 
        sn=1,
        data=[{'i': 'pre', 's': '1', 'd': 'said'}]).thenReturn(mock_serder)
    
    mock_signature = mock(
        {'qb64': 'AADi_WkHWZZZsJSm78xV8GqnXDM7roNGvOPpYzwm3eYAHjrOvhCUXyyd8_pHDzZxXG1ESOpzKQmbgx3_MYxBno4M'}
    )
    when(ctrl.signer).sign(mock_serder.raw, index=0).thenReturn(mock_signature)

    serder, sig = ctrl.approveDelegation(agent=mock_agent)
    
    assert ctrl.serder == mock_serder
    assert serder == mock_serder
    assert sig[0] == mock_signature.qb64

    unstub()

def test_controller_rotate_salty():
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
    assert 'sxlt' in out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK']
    assert out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK']['sxlt'] != "1AAH2R_SPhr_5vIBGGtyVamaGVDQAcYlgmwDOkJwM-q6Qw8K5NT7jLzJ0k6_7sa3oyKK33ym8JX1Il4MoUiy8ixYwsVWYhaU3sMT"

# def test_controller_rotate_randy():
#     ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)    

#     aid_one = {
#                "name": "aid1", 
#                "prefix": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", 
#                "randy": {
#                    "prxs": [], 
#                    "nxts": [], 
#                 },
#                 "state": {
#                     "k": ["BAzUCcD85Cs62fLeBEk6ewziVohx2kXnzuANqspIcwS2"],
#                 },
#             }
#     out = ctrl.rotate(nbran="0123456789abcdefghijk", aids=[aid_one],)

#     assert 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK' in out['keys']
#     assert 'sxlt' in out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK']
#     assert out['keys']['ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK']['sxlt'] != "1AAH2R_SPhr_5vIBGGtyVamaGVDQAcYlgmwDOkJwM-q6Qw8K5NT7jLzJ0k6_7sa3oyKK33ym8JX1Il4MoUiy8ixYwsVWYhaU3sMT"

# def test_controller_rotate_salty_pure_mock():
#     ctrl = Controller(bran="abcdefghijklmnop01234", tier=Tiers.low)

#     mock_cipher = mock()
#     from keri.core import coring
#     when(coring).Cipher(qb64="saltysalt").thenReturn(mock_cipher)

#     mock_encrypter = mock()
#     mock_decrypter = mock()
#     when(coring).Encrypter(verkey="BMNINOi3Bp2LS7c4jfliNyEdAJrQv4Aj6wzX_IkbNBvE").thenReturn(mock_encrypter)
#     when(coring).Decrypter(seed="AH7StO7quXIko8i_HfOkeJ1Zm_2kWAykYqEHg1MHJXVX").thenReturn(mock_decrypter)

#     mock_matter = mock()
#     when(coring).Matter(qb64b="0AAabcdefghijklmnop01234").thenReturn(mock_matter)
#     mock_cipher = mock({'qb64': 'cipher qb64'})
#     when(mock_encrypter).encrypt(matter=mock_matter).thenReturn(mock_cipher)

#     aid_one = {
#             "name": "aid1", 
#             "prefix": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", 
#             "salty": {
#                 "pidx": 0, 
#                 "stem":"signify:aid", 
#                 "sxlt": "1AAH2R_SPhr_5vIBGGtyVamaGVDQAcYlgmwDOkJwM-q6Qw8K5NT7jLzJ0k6_7sa3oyKK33ym8JX1Il4MoUiy8ixYwsVWYhaU3sMT",
#                 "tier": "low",
#                 "icodes": ["A"],
#                 "kidx": 0,
#                 "transferable": False,
#             },
#             "state": {
#                 "k": ["BMYrPoeKdptlDj4E4LC2KdcMX0-7SWBd-VkAGb4PYKFO"],
#             },
#         }
#     out = ctrl.rotate(nbran="0123456789abcdefghijk", aids=[aid_one],)
#     print(out)